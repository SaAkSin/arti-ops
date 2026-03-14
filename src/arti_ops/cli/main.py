import os
import sys
import asyncio
import logging
from dotenv import load_dotenv

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, RichLog
from textual.binding import Binding

from ..core.pipeline import ArtiOpsPipeline

logger = logging.getLogger(__name__)

class ArtiOpsApp(App):
    """arti-ops TUI Application"""
    
    CSS = """
    Screen {
        layout: vertical;
    }
    RichLog {
        height: 1fr;
        border: solid green;
        padding: 1;
    }
    """
    
    BINDINGS = [
        Binding("i", "input_command", "명령어/피드백 입력 (한글지원)", show=True),
        Binding("q", "quit", "종료", show=True),
        Binding("ctrl+c", "quit", "종료", show=True),
    ]

    def __init__(self, workspace: str, agent: str):
        super().__init__()
        self.workspace = workspace
        self.target_agent = agent
        self.pipeline = ArtiOpsPipeline(target_project_id=workspace)
        self.session_id = f"sess_{workspace}_{agent}"
        self.pipeline_task: asyncio.Task | None = None
        self.is_waiting_for_approval = False

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield RichLog(id="main_log", markup=True, wrap=True)
        yield Footer()

    async def on_mount(self) -> None:
        log = self.query_one(RichLog)
        log.write(f"[bold green]🚀 Target Workspace: '{self.workspace}' / Agent: '{self.target_agent}' 로컬 컨텍스트 융합 TUI 앱에 오신 것을 환영합니다.[/bold green]")
        log.write("[italic]하단 단축키(i)를 눌러 프롬프트 창을 띄운 후 지시를 입력하세요. (예: '현재 프로젝트 구조를 참고해서 DB 연동 스킬을 만들어줘')[/italic]")

    async def action_input_command(self) -> None:
        """한글 입력 깨짐 방지를 위해 TUI를 잠시 내리고 기본 터미널 입력(Native IME)을 받습니다."""
        with self.suspend():
            print("\n=======================================================")
            print("[ TUI 임시 중단 - 자연어 명령어/피드백 입력 모드 ]")
            print("=======================================================")
            print("💡 한글 정상 입력을 위해 터미널 기본 모드로 진입했습니다.")
            print("   - 피드백이나 지시사항을 자유롭게 한글로 입력하세요.")
            print("   - 내용 없이 [Enter]만 누르면 TUI 화면으로 복귀합니다.")
            print("   - 'q' 입력 시 앱이 완전히 종료됩니다.")
            print("-------------------------------------------------------\n")
            try:
                user_input = input("📝 프롬프트 ❯ ")
            except EOFError:
                user_input = ""
                
        user_input = user_input.strip()
        if user_input:
            if user_input.lower() == 'q':
                self.exit()
                return
            await self._process_input(user_input)

    async def _process_input(self, user_input: str) -> None:
        log = self.query_one(RichLog)
        
        if self.is_waiting_for_approval:
            # 피드백 또는 승인 처리 (Self-Correction 루프)
            if user_input.lower() in ['y', 'yes', '승인', 'yep', 'ㅇㅇ']:
                log.write("\n[bold green]✅ 승인 완료. Executor(샌드박스/파일 배포) 단계를 가동합니다.[/bold green]\n")
                self.is_waiting_for_approval = False
                await self.pipeline.resume(self.session_id, {"approved": True})
            elif user_input.lower() in ['n', 'no', '반려', '거절', 'ㄴㄴ']:
                log.write("\n[bold red]❌ 배포 단순 취소. 파이프라인을 종료합니다.[/bold red]\n")
                self.is_waiting_for_approval = False
                await self.pipeline.resume(self.session_id, {"approved": False, "feedback": "사용자가 TUI에서 수동으로 승인을 반려했습니다."})
            else:
                log.write(f"\n[bold magenta]💬 피드백 전달 완료. Architect에게 재기획 지시: '{user_input}'[/bold magenta]\n")
                log.write("[italic]...다시 생성 중입니다...[/italic]")
                self.is_waiting_for_approval = False
                await self.pipeline.resume(self.session_id, {"approved": False, "feedback": user_input})
            return
            
        # 첫 파이프라인 가동
        if self.pipeline_task is None or self.pipeline_task.done():
            # 사용자의 지시를 반영한 초기 프롬프트 구성
            command_prompt = (
                f"사용자가 다음과 같은 지시를 내렸습니다:\n"
                f"\"{user_input}\"\n\n"
                f"Target Workspace: `{self.workspace}`\n"
                f"타겟 에이전트: `{self.target_agent}`\n"
                f"위 지시를 바탕으로 로컬 현황과 BookStack 정책을 조사하여 새로운 룰/스킬을 생성하거나 수정하세요."
            )
            log.write(f"\n[bold yellow]▶ 사용자 지시: {user_input}[/bold yellow]")
            
            # 파이프라인 비동기 태스크 실행
            self.pipeline_task = asyncio.create_task(self.run_pipeline_bg(command_prompt))
        else:
            log.write("[yellow]⚠️ 이미 파이프라인이 동작 중입니다. 잠시만 기다려주세요.[/yellow]")

    async def run_pipeline_bg(self, command_prompt: str):
        log = self.query_one(RichLog)
        try:
            async for event in self.pipeline.run(command_prompt=command_prompt, session_id=self.session_id):
                if isinstance(event, dict):
                    e_type = event.get("type")
                    status = event.get("status")
                    
                    if e_type == "phase_start":
                        log.write(f"[bold cyan]▶ [{event.get('agent')}] 시작: {event.get('message')}[/bold cyan]")
                    elif e_type == "tool_call":
                        log.write(f"  [dim]🔧 내부 도구 호출: {event.get('tool_name')}[/dim]")
                    elif e_type == "phase_end":
                        color = "green" if event.get("status") == "success" else "red"
                        log.write(f"[bold {color}]✔ [{event.get('agent')}] 단계 완료 ({event.get('status')})[/bold {color}]\n")
                    
                    elif status == "pending_final_approval":
                        # 검증 완료 후 최종 보고서 출력
                        log.write("\n[bold yellow]🔔 [사전 검토 및 반영 판단 대기][/bold yellow]")
                        
                        # 파이프라인에서 report를 추출하여 보여준다.
                        if "report" in event:
                            report_text = event["report"]
                            log.write("[bold white]--- 📄 [최종 검토 보고서] ---[/bold white]")
                            log.write(report_text)
                            log.write("[bold white]-----------------------------[/bold white]")
                        else:
                            log.write("[dim]산출물 상세 내용이 없습니다.[/dim]")
                            
                        log.write("  ▶ 승인 후 배포 진행: [bold green]Y (또는 승인)[/bold green]")
                        log.write("  ▶ 추가 수정 지시(재생성): [bold cyan]원하는 수정 방향을 구체적인 자연어로 입력하세요.[/bold cyan]")
                        
                        self.is_waiting_for_approval = True
                        
                elif getattr(event, "content", None) and getattr(event.content, "parts", None):
                    # 내부 스트리밍 로직은 무시하거나 아주 은은하게 표시할 수도 있음. TUI 가독성을 위해 생략.
                    pass
                    
            log.write("\n[bold green]✅ 모든 작업이 종료되었습니다. 프롬프트에 추가 명령을 입력하거나 'q'를 눌러 종료하세요.[/bold green]")
        except asyncio.CancelledError:
            log.write("\n[bold red]파이프라인이 취소되었습니다.[/bold red]")
        except Exception as e:
            logger.exception("파이프라인 실행 중 오류")
            log.write(f"\n[bold red]❌ 파이프라인 에러 발생: {e}[/bold red]")

def main():
    load_dotenv()
    os.makedirs("logs", exist_ok=True)
    logging.basicConfig(
        filename="logs/arti-ops-tui.log",
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # workspace 결정
    # 1. 인자로 넘어온 경우
    # 2. 없으면 os.path.basename(os.getcwd())
    workspace = sys.argv[1] if len(sys.argv) > 1 else os.path.basename(os.getcwd())
    agent = sys.argv[2] if len(sys.argv) > 2 else "antigravity"
    
    app = ArtiOpsApp(workspace=workspace, agent=agent)
    app.run()

if __name__ == "__main__":
    main()
