from textual import on, events
import argparse
import asyncio
import os
import logging
from itertools import cycle
from dotenv import load_dotenv
from textual.app import App, ComposeResult
from textual.containers import VerticalScroll, Container
from textual.widgets import Header, Footer, Label, Static, Collapsible
from rich.markdown import Markdown

SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

class AgentBlock(Container):
    """
    [SSH 최적화 블록]
    1. DOM 격리: 무거운 Collapsible을 건드리지 않고 가벼운 Label만 갱신하여 렉 원천 차단.
    2. 지연 렌더링(Lazy Loading): 마크다운 파싱은 사용자가 아코디언을 클릭해 열 때 단 1회만 수행.
    """
    def __init__(self, role: str, initial_text: str=""):
        super().__init__()
        self.role_name = role
        self.icon = "⚙️" if "system" in role.lower() else "👤" if "user" in role.lower() else "🤖"
        self._full_text = initial_text
        self._is_generating = True
        self._is_rendered = False
        self._spinner = cycle(SPINNER_FRAMES)
        
        # 지속적으로 업데이트될 가벼운 라벨 위젯 (화면 Reflow 방지)
        self.header_label = Label(f"{next(self._spinner)} {self.icon} [{self.role_name}] 작업 준비 중...", classes="header_label")
        
        # 렌더링 부하를 없애기 위해 초기엔 빈 텍스트로 생성
        self.content_widget = Static("", classes="chat_content")
        self.collapsible = Collapsible(self.content_widget, title="👉 상세 로그 펼치기 (클릭 또는 Enter)", collapsed=True)

    def compose(self) -> ComposeResult:
        yield self.header_label
        yield self.collapsible

    def on_mount(self) -> None:
        # 애니메이션 타이머 등록 (0.15초)
        self.anim_timer = self.set_interval(0.15, self._animate_spinner)
        # 생성 중에는 불필요한 UI 조작을 막기 위해 아코디언 자체를 숨김
        self.collapsible.display = False 

    def _animate_spinner(self):
        if self._is_generating:
            frame = next(self._spinner)
            bytes_len = len(self._full_text.encode('utf-8'))
            if bytes_len > 0:
                self.header_label.update(f"[bold cyan]{frame} {self.icon} [{self.role_name}] 텍스트 생성 중... ({bytes_len} Bytes)[/bold cyan]")
            else:
                self.header_label.update(f"[bold cyan]{frame} {self.icon} [{self.role_name}] 에이전트 초기화 중...[/bold cyan]")

    def append_text(self, text: str):
        # 화면 조작 없이 문자열 버퍼에만 조용히 누적
        self._full_text += text

    def _get_summary(self) -> str:
        """출력된 내용 중 의미 있는 첫 문장 추출"""
        lines = [line.strip() for line in self._full_text.splitlines() 
                 if line.strip() and not line.strip().startswith("```") and not line.strip().startswith("#")]
        if lines:
            first_line = lines[0]
            return first_line[:55] + "..." if len(first_line) > 55 else first_line
        return "완료 (내용 없음)"

    def mark_complete(self):
        """에이전트 턴 종료 시 애니메이션 중지 및 요약문 노출"""
        if not self._is_generating: 
            return
            
        self._is_generating = False
        if hasattr(self, 'anim_timer'):
            self.anim_timer.pause()
            
        summary = self._get_summary() if self._full_text.strip() else "출력 없음"
        
        # 상태를 고정된 요약 텍스트로 변환
        self.header_label.update(f"[bold green]✅ {self.icon} [{self.role_name}] 요약: {summary}[/bold green]")
        
        if self._full_text.strip():
            self.collapsible.display = True # 이제 클릭하여 펼칠 수 있도록 노출
            
        if self.app:
            try:
                self.app.query_one("#chat_container", VerticalScroll).scroll_end(animate=True)
            except Exception:
                pass

    @on(Collapsible.Toggled)
    def render_markdown_lazy(self, event: Collapsible.Toggled) -> None:
        """사용자가 아코디언을 열었을 때 비로소 마크다운 렌더링 수행 (Lazy Loading)"""
        if not event.collapsible.collapsed and not self._is_rendered:
            self.content_widget.update(Markdown(self._full_text))
            self._is_rendered = True
            self.app.query_one("#chat_container", VerticalScroll).scroll_end(animate=True)


class ArtiOpsApp(App):
    CSS = """
    Screen { background: $surface; }
    #chat_container { height: 1fr; padding: 1 2; overflow-y: scroll; }
    AgentBlock { margin-top: 1; margin-bottom: 1; background: $panel; border-left: thick $accent; padding: 1 2; }
    .header_label { margin-bottom: 1; }
    Collapsible { border-top: solid $surface; padding-top: 1; }
    .chat_content { margin-left: 2; padding-top: 1; padding-bottom: 1; }
    #status_bar { dock: bottom; height: 1; padding: 0 1; background: $accent; color: $text; text-style: bold; }
    """
    
    # 하단 Footer에 단축키 명시 (리눅스 터미널 시인성 향상 및 포커스 이탈 대비)
    BINDINGS = [
        ("q", "quit", "종료(Q)"),
        ("y", "approve", "배포 승인(Y)"),
        ("n", "reject", "승인 반려(N)"),
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
        yield Footer() # 사용자 시인성 확보를 위한 푸터 추가

    async def on_mount(self) -> None:
        self.title = "arti-ops v0.1.7"
        self.sub_title = "Cross-Platform AgentOps (macOS/Linux) - Lazy Render"
        
        sys_bubble = AgentBlock(role="System", initial_text="최신 정책 융합 및 배포 파이프라인 엔진을 가동합니다...")
        await self.chat_container.mount(sys_bubble)
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
                    self.status_bar.update("🔔 [HITL 대기] GWS 승인 요청됨: 하단 단축키를 눌러 승인(Y) 또는 반려(N)를 진행하세요.")
                    self.waiting_for_approval = True
                    # 승인 대기 상태일 때는 내용을 즉시 검토할 수 있도록 현재 버블을 강제로 엽니다.
                    if self.current_ai_bubble and self.current_ai_bubble.collapsible.display:
                        self.current_ai_bubble.collapsible.collapsed = False
                    continue

                if text_output:
                    # 새로운 역할(Agent)로 스위치될 때만 새로운 블록 마운트
                    if not self.current_ai_bubble or getattr(self.current_ai_bubble, 'role_name', None) != role_title:
                        if self.current_ai_bubble:
                            self.current_ai_bubble.mark_complete()
                                
                        self.current_ai_bubble = AgentBlock(role=role_title, initial_text="")
                        await self.chat_container.mount(self.current_ai_bubble)
                        
                    self.current_ai_bubble.append_text(text_output)
                
            if self.current_ai_bubble:
                self.current_ai_bubble.mark_complete()

            if not self.waiting_for_approval:
                self.status_bar.update("✅ 배포 완료! [Q]를 눌러 종료하세요.")
                
        except Exception as e:
            err_bubble = AgentBlock(role="System_Error", initial_text=f"**Error Occurred:**\n```\n{str(e)}\n```")
            await self.chat_container.mount(err_bubble)
            err_bubble.mark_complete()
            # 에러는 강제로 펼쳐서 보여줌
            if err_bubble.collapsible.display:
                err_bubble.collapsible.collapsed = False 
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
