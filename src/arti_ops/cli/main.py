import os
import asyncio
import logging
from dotenv import load_dotenv

from cyclopts import App as CycloptsApp
from prompt_toolkit import PromptSession, prompt
from prompt_toolkit.completion import WordCompleter
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from ..core.pipeline import ArtiOpsPipeline

# Cyclopts CLI 앱 선언
app = CycloptsApp(name="arti-ops", help="ADK 기반 다중 프로젝트 정책 병합 플랫폼 (대화형 CLI)")
console = Console()

async def _run_pipeline(workspace: str):
    pipeline = ArtiOpsPipeline(target_project_id=workspace)
    session_id = f"sess_{workspace}"
    
    console.print(f"\n[bold green]� Target Workspace: '{workspace}' 정책 동기화 파이프라인 가동...[/bold green]\n")
    
    current_agent = None
    buffer_text = ""
    # Rich의 Status 기능을 이용한 부드러운 텍스트 스피너 (SSH 렉 완전 방지)
    status = console.status("[bold cyan]파이프라인 및 에이전트 초기화 중...[/bold cyan]")
    status.start()
    
    try:
        command_prompt = f"Target Workspace: `{workspace}` 에 대해 L1, L2 룰을 융합하고 배포를 시작하세요."
        async for event in pipeline.run(command_prompt=command_prompt, session_id=session_id):
            
            # HITL (Pause) 상태 감지
            is_paused = False
            if isinstance(event, dict) and event.get("status") == "pending_approval":
                is_paused = True
            elif getattr(event, "__class__", None) and getattr(event.__class__, "__name__", "") == "PauseEvent":
                is_paused = True

            if is_paused:
                status.stop() # 입력 대기를 위해 스피너 정지
                
                # 정지 직전까지 모인 버퍼 텍스트 깔끔하게 패널로 출력
                if buffer_text.strip() and current_agent and current_agent != "System":
                    console.print(Panel(Markdown(buffer_text), title=f"🤖 Agent ({current_agent}) 산출물", border_style="blue"))
                    buffer_text = ""
                
                console.print("\n[bold yellow]🔔 [HITL 승인 대기] 파괴적 변경이나 충돌이 감지되었습니다.[/bold yellow]")
                console.print("  ▶ 배포 승인 및 진행: [bold green]Y[/bold green] (또는 Enter)")
                console.print("  ▶ 단순 배포 취소: [bold red]N[/bold red]")
                console.print("  ▶ 에이전트 수정 지시: [bold cyan]요구사항을 직접 타이핑하세요 (예: '로그 포맷 바꿔줘')[/bold cyan]")
                
                # prompt_toolkit을 활용한 블로킹 없는 비동기 프롬프트 입력
                session = PromptSession()
                user_input = await session.prompt_async('📝 피드백 입력 ❯ ')
                user_input = user_input.strip()
                
                if user_input.lower() in ['y', 'yes', '승인', '']:
                    console.print("\n[bold green]✅ 승인 완료. Executor 배포를 진행합니다.[/bold green]\n")
                    await pipeline.resume(session_id, {"approved": True})
                elif user_input.lower() in ['n', 'no', '반려', '거절']:
                    console.print("\n[bold red]❌ 승인 거절. 파이프라인을 단순 반려합니다.[/bold red]\n")
                    await pipeline.resume(session_id, {"approved": False, "feedback": "관리자가 무조건 거절함"})
                else:
                    # 자연어 피드백을 전달하여 While 루프(Self-Correction)가 다시 돌도록 유도
                    console.print(f"\n[bold magenta]💬 피드백 전달 완료. 에이전트 재기획 지시: '{user_input}'[/bold magenta]\n")
                    await pipeline.resume(session_id, {"approved": False, "feedback": user_input})
                
                status.start() # 작업 재개 스피너 가동
                continue

            # 에이전트 텍스트 토큰 추출
            text_output = ""
            if getattr(event, "content", None) and getattr(event.content, "parts", None):
                text_output = "".join([part.text for part in event.content.parts if part.text])
            
            agent_name = getattr(event, "author", "System")
            
            ROLE_NAMES_KR = {
                "context_profiler": "컨텍스트 분석기",
                "skill_architect": "스킬 기획자",
                "critical_verifier": "정책 검증기",
                "deployment_executor": "배포 실행기",
                "system": "시스템"
            }
            
            if agent_name.lower() == "user":
                role_title = "시스템"
            else:
                base_name = agent_name.lower()
                role_title = ROLE_NAMES_KR.get(base_name, agent_name)

            # 에이전트가 교체될 때 기존 버퍼를 패널로 감싸서 한 번에 출력 (Summary-like effect)
            if current_agent != role_title:
                if buffer_text.strip() and current_agent and current_agent != "System":
                    status.stop()
                    console.print(Panel(Markdown(buffer_text), title=f"🤖 Agent ({current_agent}) 산출물", border_style="green"))
                    status.start()
                buffer_text = ""
                current_agent = role_title
            
            # 텍스트 누적 및 스피너 바이트 수 갱신 (화면 덜컹거림 원천 차단)
            if text_output:
                buffer_text += text_output
                status.update(f"[bold cyan]⏳ Agent ({current_agent}) 작업 중... ({len(buffer_text.encode('utf-8'))} Bytes)[/bold cyan]")
                
        # 루프 완전 종료 후 마지막 버퍼 출력
        status.stop()
        if buffer_text.strip() and current_agent and current_agent != "System":
            console.print(Panel(Markdown(buffer_text), title=f"🤖 Agent ({current_agent}) 최종 완료", border_style="green"))
            
        console.print("\n[bold green]🎉 모든 파이프라인 작업이 성공적으로 종료되었습니다![/bold green]")
        
    except Exception as e:
        status.stop()
        console.print_exception(show_locals=False)
        console.print(f"\n[bold red]❌ 파이프라인 실행 중 오류가 발생했습니다: {e}[/bold red]")

@app.command
def sync(workspace: str = None):
    """
    사내 BookStack에 정의된 L1/L2 정책을 로컬 환경에 병합하고 배포합니다.
    
    Args:
        workspace: 동기화할 타겟 프로젝트 ID. 누락 시 대화형 자동완성 프롬프트가 실행됩니다.
    """
    # 워크스페이스 미입력 시 prompt_toolkit 자동완성 프롬프트 실행 (동기 컨텍스트)
    if not workspace:
        # 향후 BookStack API 연동하여 실제 프로젝트 리스트 Fetch 연동 포인트
        available_projects = ["Project_Alpha", "Project_Beta", "Core_Backend", "Frontend_Web"]
        completer = WordCompleter(available_projects, ignore_case=True)
        
        console.print("[yellow]💡 타겟 워크스페이스가 지정되지 않았습니다.[/yellow]")
        workspace = prompt(
            '동기화할 프로젝트 ID를 입력하세요 (Tab 키로 자동완성): ', 
            completer=completer
        ).strip()
        
        if not workspace:
            console.print("[bold red]❌ 워크스페이스 입력이 취소되었습니다.[/bold red]")
            return

    # 비동기 이벤트 루프 실행
    asyncio.run(_run_pipeline(workspace))

def main():
    load_dotenv()
    os.makedirs("logs", exist_ok=True)
    # TUI가 아니므로 파일 이름 변경 적용
    logging.basicConfig(
        filename="logs/arti-ops-cli.log",
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Cyclopts 앱 구동 (sys.argv 자동 파싱)
    app()

if __name__ == "__main__":
    main()
