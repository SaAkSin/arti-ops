from textual import events
import argparse
import asyncio
import os
import logging
from itertools import cycle
from dotenv import load_dotenv
from textual.app import App, ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Header, Label, Static, Collapsible
from rich.markdown import Markdown

# 리눅스/macOS 터미널 모두에서 호환되는 점자 스피너 프레임
SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

class ChatBubble(Collapsible):
    """UI 렉을 원천 차단하기 위해 텍스트 생성 중에는 접어두고 스피너만 보여주는 스마트 블록"""
    def __init__(self, role: str, initial_text: str=""):
        self.role_name = role
        self.icon = "⚙️" if "system" in role.lower() else "👤" if "user" in role.lower() else "🤖"
        
        # 렌더링 부하를 막기 위해 생성 즉시 아코디언을 닫아둠(collapsed=True)
        super().__init__(title=f"{self.icon} [{self.role_name}] 준비 중...", collapsed=True)
        
        self._full_text = initial_text
        self.content_widget = Static(Markdown(""), classes="chat_content")
        
        self._spinner = cycle(SPINNER_FRAMES)
        self._anim_timer = None
        self._is_generating = True

    def compose(self) -> ComposeResult:
        yield self.content_widget

    def on_mount(self) -> None:
        # 본문 렌더링 대신, 타이틀의 스피너만 0.1초마다 돌려 CPU 및 SSH 대역폭 소모 최소화
        self._anim_timer = self.set_interval(0.1, self._animate_spinner)

    def _animate_spinner(self):
        if self._is_generating:
            frame = next(self._spinner)
            bytes_len = len(self._full_text.encode('utf-8'))
            if bytes_len > 0:
                self.title = f"{frame} {self.icon} [{self.role_name}] 응답 생성 중... ({bytes_len} Bytes)"
            else:
                self.title = f"{frame} {self.icon} [{self.role_name}] 생각 중..."

    def append_text(self, text: str):
        # 화면을 다시 그리지 않고 텍스트는 메모리 버퍼에만 조용히 누적
        self._full_text += text

    def _get_summary(self) -> str:
        """마크다운 문법을 제외한 핵심 첫 문장을 요약문으로 추출"""
        lines = [line.strip() for line in self._full_text.splitlines() 
                 if line.strip() and not line.strip().startswith("```") and not line.strip().startswith("#")]
        if lines:
            first_line = lines[0]
            return first_line[:45] + "..." if len(first_line) > 45 else first_line
        return "완료 (내용 없음)"

    def mark_complete(self):
        """에이전트 턴 종료 시 애니메이션 중지 및 단 1회만 마크다운 렌더링 수행"""
        if not self._is_generating:
            return
            
        self._is_generating = False
        if self._anim_timer:
            self._anim_timer.pause()
            
        # SSH 터미널 화면이 덜컹거리지 않도록 단 한 번만 렌더링
        if self._full_text.strip():
            self.content_widget.update(Markdown(self._full_text))
            summary = self._get_summary()
        else:
            self.content_widget.update(Markdown("*출력된 내용이 없습니다.*"))
            summary = "상태 업데이트 완료"
            
        # 요약 결과를 제목에 띄우고 계속 닫아둠 (클릭하면 펼쳐짐)
        self.title = f"✅ {self.icon} [{self.role_name}] 요약: {summary}"
        self.collapsed = True
        
        # 스크롤 최하단 유지
        if self.app:
            try:
                self.app.query_one("#chat_container", VerticalScroll).scroll_end(animate=True)
            except Exception:
                pass

class ArtiOpsApp(App):
    CSS = """
    Screen { background: $surface; }
    #chat_container { height: 1fr; padding: 1 2; overflow-y: scroll; }
    ChatBubble { margin-top: 1; margin-bottom: 1; background: $panel; border-left: thick $accent; }
    .chat_content { margin-left: 2; padding-top: 1; padding-bottom: 1; }
    #status_bar { dock: bottom; height: 1; padding: 0 1; background: $accent; color: $text; text-style: bold; }
    """
    
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
        self.title = "arti-ops v0.1.5"
        self.sub_title = "Cross-Platform AgentOps (macOS/Linux)"
        
        sys_bubble = ChatBubble(role="System", initial_text="최신 정책 융합 및 배포 파이프라인 엔진을 가동합니다...")
        await self.chat_container.mount(sys_bubble) # 🚨 await 필수
        sys_bubble.mark_complete()
        
        prompt = f"Target Workspace: `{self.target_project}` 에 대해 L1, L2 룰을 융합하고 배포를 시작합니다."
        asyncio.create_task(self.run_pipeline(prompt))

    async def action_approve(self):
        if self.waiting_for_approval:
            self.waiting_for_approval = False
            self.status_bar.update("✅ 승인 완료. 파이프라인을 재개합니다...")
            await self.pipeline.resume(self.pipeline_session_id, {"approved": True})

    async def action_reject(self):
        if self.waiting_for_approval:
            self.waiting_for_approval = False
            self.status_bar.update("❌ 승인 거절. 파이프라인이 반려되었습니다.")
            await self.pipeline.resume(self.pipeline_session_id, {"approved": False})

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
                role_title = f"{agent_name}" if agent_name and agent_name.lower() != "user" else "System"

                is_paused = False
                if isinstance(event, dict) and event.get("status") == "pending_approval":
                    is_paused = True
                elif getattr(event, "__class__", None) and getattr(event.__class__, "__name__", "") == "PauseEvent":
                    is_paused = True

                if is_paused:
                    self.status_bar.update("🔔 [HITL 대기] GWS 승인 요청됨: 진행 [Y], 반려 [N] 입력")
                    self.waiting_for_approval = True
                    continue

                if text_output:
                    if not self.current_ai_bubble or getattr(self.current_ai_bubble, 'role_name', None) != role_title:
                        
                        # 🚨 비동기 DOM 조작 (await 추가)
                        if self.current_ai_bubble:
                            if not self.current_ai_bubble._full_text.strip():
                                await self.current_ai_bubble.remove()
                            else:
                                self.current_ai_bubble.mark_complete()
                                
                        self.current_ai_bubble = ChatBubble(role=role_title, initial_text="")
                        await self.chat_container.mount(self.current_ai_bubble)
                        
                    self.current_ai_bubble.append_text(text_output)
                
            if self.current_ai_bubble:
                self.current_ai_bubble.mark_complete()

            if not self.waiting_for_approval:
                self.status_bar.update("✅ 배포 완료! [Q]를 눌러 종료하세요.")
                
        except Exception as e:
            err_bubble = ChatBubble(role="System_Error", initial_text=f"**Error Occurred:**\n```\n{str(e)}\n```")
            err_bubble.mark_complete()
            await self.chat_container.mount(err_bubble)
            self.chat_container.scroll_end(animate=False)
            self.status_bar.update("❌ Pipeline Failed.")

def main():
    load_dotenv()
    os.makedirs("logs", exist_ok=True)
    logging.basicConfig(
        filename="logs/arti-ops-tui.log",
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
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
