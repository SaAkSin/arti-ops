from textual import events
import argparse
import asyncio
import os
import logging
from dotenv import load_dotenv
from textual.app import App, ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Header, Label, Static, Collapsible
from rich.markdown import Markdown

class ChatBubble(Collapsible):
    """0.15초 단위 버퍼링(Throttling)을 적용하여 렌더링 렉을 유발하지 않는 아코디언 블록"""
    def __init__(self, role: str, initial_text: str=""):
        icon = "⚙️" if "system" in role.lower() else "👤" if "user" in role.lower() else "🤖"
        super().__init__(title=f"{icon} {role} (Generating...)")
        self.role = role
        self._full_text = initial_text
        self._rendered_text = initial_text
        self.content_widget = Static(Markdown(self._full_text), classes="chat_content")
        self._flush_timer = None

    def compose(self) -> ComposeResult:
        yield self.content_widget

    def on_mount(self) -> None:
        # 0.15초마다 버퍼를 확인하여 화면 갱신 (마크다운 무한 파싱 부하 최소화)
        self._flush_timer = self.set_interval(0.15, self._flush)

    def append_text(self, text: str):
        self._full_text += text

    def _flush(self):
        # 내용이 변경되었을 때만 렌더링 (병목 방지)
        if self._full_text != self._rendered_text:
            self._rendered_text = self._full_text
            self.content_widget.update(Markdown(self._rendered_text))
            
            # 애니메이션 끄기로 부드러운 하단 추적 유지
            if self.app:
                try:
                    self.app.query_one("#chat_container", VerticalScroll).scroll_end(animate=False)
                except Exception:
                    pass

    def mark_complete(self):
        """에이전트 턴 종료 시 생명주기 마감 및 접기"""
        if self._flush_timer:
            self._flush_timer.pause()
        self._flush()
        self.title = self.title.replace("(Generating...)", "(Completed)")
        self.collapsed = True

class ArtiOpsApp(App):
    # CSS 유지
    CSS = """
    Screen { background: $surface; }
    #chat_container { height: 1fr; padding: 1 2; overflow-y: scroll; }
    ChatBubble { margin-top: 1; margin-bottom: 1; background: $panel; border-left: thick $accent; }
    .chat_content { margin-left: 2; padding-top: 1; padding-bottom: 1; }
    #status_bar { dock: bottom; height: 1; padding: 0 1; background: $accent; color: $text; text-style: bold; }
    """
    
    # 전역 BINDING으로 포커스 이탈 방지 (on_key 제거 및 액션 매핑)
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("ctrl+c", "quit", "Quit"),
        ("y", "approve", "Approve (HITL)"),
        ("n", "reject", "Reject (HITL)"),
    ]

    def __init__(self, target_project: str):
        super().__init__()
        self.target_project = target_project
        self.chat_container = VerticalScroll(id="chat_container")
        self.status_bar = Label(f"🚀 Ready to sync: {self.target_project}", id="status_bar")
        self.current_ai_bubble = None
        self.pipeline = None
        self.pipeline_session_id = None
        self.waiting_for_approval = False

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield self.chat_container
        yield self.status_bar

    async def on_mount(self) -> None:
        self.title = "arti-ops v0.1.2"
        self.sub_title = "ADK Policy Sync Environment"
        
        sys_bubble = ChatBubble(role="System", initial_text="최신 정책 융합 및 배포 파이프라인 엔진을 가동합니다...")
        self.chat_container.mount(sys_bubble)
        sys_bubble.mark_complete()
        
        prompt = f"Target Workspace: `{self.target_project}` 에 대해 L1, L2 룰을 융합하고 배포를 시작합니다."
        asyncio.create_task(self.run_pipeline(prompt))

    # on_key 대신 명시적 Action 정의
    def action_approve(self):
        if self.waiting_for_approval:
            self.waiting_for_approval = False
            self.status_bar.update("✅ 승인 완료. 파이프라인을 재개합니다...")
            asyncio.create_task(self.pipeline.resume(self.pipeline_session_id, {"approved": True}))

    def action_reject(self):
        if self.waiting_for_approval:
            self.waiting_for_approval = False
            self.status_bar.update("❌ 승인 거절. 파이프라인이 반려되었습니다.")
            asyncio.create_task(self.pipeline.resume(self.pipeline_session_id, {"approved": False}))

    async def run_pipeline(self, prompt: str) -> None:
        from ..core.pipeline import ArtiOpsPipeline
        try:
            self.status_bar.update("⏳ Pipeline is running... Please wait.")
            self.pipeline = ArtiOpsPipeline(target_project_id=self.target_project)
            self.pipeline_session_id = f"sess_{self.target_project}"
            
            async for event in self.pipeline.run(command_prompt=prompt, session_id=self.pipeline_session_id):
                text_output = ""
                if getattr(event, "content", None) and getattr(event.content, "parts", None):
                    text_output = "".join([part.text for part in event.content.parts if part.text])
                
                agent_name = getattr(event, "author", "Pipeline")
                role_title = f"Agent ({agent_name})" if agent_name and agent_name.lower() != "user" else "System"

                is_paused = False
                if isinstance(event, dict) and event.get("status") == "pending_approval":
                    is_paused = True
                elif getattr(event, "__class__", None) and getattr(event.__class__, "__name__", "") == "PauseEvent":
                    is_paused = True

                if is_paused:
                    self.status_bar.update("🔔 GWS 승인 요청 대기 중: 진행하려면 [Y], 취소하려면 [N]을 누르세요.")
                    self.waiting_for_approval = True
                    continue

                if text_output:
                    if not self.current_ai_bubble or self.current_ai_bubble.role != role_title:
                        
                        # 이전 버블 정리 (가비지 컬렉션: 텍스트가 없는 빈 껍데기는 삭제)
                        if self.current_ai_bubble:
                            if not self.current_ai_bubble._full_text.strip():
                                self.current_ai_bubble.remove()
                            else:
                                self.current_ai_bubble.mark_complete()
                                
                        self.current_ai_bubble = ChatBubble(role=role_title, initial_text="")
                        self.chat_container.mount(self.current_ai_bubble)
                        
                    self.current_ai_bubble.append_text(text_output)
                
            if self.current_ai_bubble:
                self.current_ai_bubble.mark_complete()

            if not self.waiting_for_approval:
                self.status_bar.update("✅ Done! You can exit by pressing 'q'.")
                
        except Exception as e:
            err_bubble = ChatBubble(role="System", initial_text=f"**Error Occurred:**\n```\n{str(e)}\n```")
            err_bubble.mark_complete()
            self.chat_container.mount(err_bubble)
            self.chat_container.scroll_end(animate=False)
            self.status_bar.update("❌ Pipeline Failed.")

def main():
    # .env 환경 변수 로드 (명령어 진입점이므로 가장 먼저 실행)
    load_dotenv()
    
    # 로그 디렉토리 보장 및 파일 로깅 설정 (TUI 화면 깨짐 방지 위해 파일로만 기록)
    os.makedirs("logs", exist_ok=True)
    logging.basicConfig(
        filename="logs/arti-ops-tui.log",
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Textual 내부 에러 로그 등도 파일에 남기도록 설정 가능
    # os.environ["TEXTUAL_LOG"] = "logs/textual.log"

    parser = argparse.ArgumentParser(description="arti-ops: ADK AgentOps Platform CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    sync_parser = subparsers.add_parser("sync", help="Synchronize L1/L2 policies to local workspace")
    sync_parser.add_argument("--workspace", required=True, help="Target project/workspace ID to sync")
    
    args = parser.parse_args()
    
    if args.command == "sync":
        app = ArtiOpsApp(target_project=args.workspace)
        app.run()

if __name__ == "__main__":
    main()
