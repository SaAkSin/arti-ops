import argparse
import asyncio
from textual.app import App, ComposeResult
from textual.containers import Container, VerticalScroll
from textual.widgets import Header, Footer, Log, Label, Static

class ArtiOpsApp(App):
    """
    arti-ops TUI 애플리케이션
    에이전트들의 진행 상황을 실시간 스트리밍으로 렌더링합니다.
    """
    CSS = """
    Screen {
        layout: vertical;
    }
    #main_container {
        height: 1fr;
        padding: 1 2;
    }
    Log {
        border: solid green;
        height: 1fr;
    }
    .status_label {
        padding: 1;
        text-style: bold;
        color: cyan;
    }
    """
    
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("ctrl+c", "quit", "Quit")
    ]

    def __init__(self, target_project: str):
        super().__init__()
        self.target_project = target_project
        self.status_label = Label(f"Target Project: {self.target_project}", classes="status_label")
        self.log_view = Log(id="agent_log")
        
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(id="main_container"):
            yield self.status_label
            yield self.log_view
        yield Footer()

    async def on_mount(self) -> None:
        self.title = "arti-ops v0.1.0 Platform"
        self.sub_title = "ADK Policy Sync Environment"
        self.log_view.write_line("🚀 [System] Initializing Antigravity Agent Crew...")
        
        # 여기서 파이프라인 비동기 실행 스레드/태스크를 예약해 스트리밍 이벤트를 받습니다.
        asyncio.create_task(self.run_pipeline())

    async def run_pipeline(self) -> None:
        from ..core.pipeline import PartiOpsPipeline
        try:
            pipeline = PartiOpsPipeline(target_project_id=self.target_project)
            prompt = f"Target Workspace: {self.target_project} 에 대해 L1, L2 룰을 융합하고 로컬에 배포할 준비를 하세요."
            
            async for event in pipeline.run(command_prompt=prompt):
                # Textual Log 위젯에 로그와 메세지 스트림 작성
                # Event 객체의 타입에 따라 메세지 포맷팅
                self.log_view.write_line(f"Event: {event}")
                
            self.log_view.write_line("✅ [System] Pipeline execution completed. You can quit (q) now.")
        except Exception as e:
            self.log_view.write_line(f"❌ [Error] {str(e)}")

def main():
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
