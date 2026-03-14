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
from rich.tree import Tree
from rich.live import Live

from ..core.pipeline import ArtiOpsPipeline

# Cyclopts CLI 앱 선언
app = CycloptsApp(name="arti-ops", help="ADK 기반 다중 프로젝트 정책 병합 플랫폼 (대화형 CLI)")
console = Console()

async def _run_pipeline(workspace: str, target_agent: str):
    pipeline = ArtiOpsPipeline(target_project_id=workspace)
    session_id = f"sess_{workspace}_{target_agent}"
    
    console.print(f"\n[bold green]🚀 Target Workspace: '{workspace}' (Agent: {target_agent}) 정책 동기화 가동...[/bold green]\n")
    
    # 1. 기본 트리 구조 셋업
    main_tree = Tree(f"🚀 [bold blue]{workspace} (Agent: {target_agent}) 파이프라인 진행 상태[/bold blue]")
    nodes = {}
    
    agents_info = [
        ("context_profiler", "🕵️ Context Profiler"), 
        ("skill_architect", "🧠 Skill Architect"), 
        ("critical_verifier", "🧐 Critical Verifier"), 
        ("deployment_executor", "🚀 Deployment Executor")
    ]
    
    # 에이전트 초기화 (대기 상태 렌더링)
    for agent_key, name in agents_info:
        nodes[agent_key] = main_tree.add(f"[dim]⏸️  {name} (대기중)[/dim]")
        
    console.print("\n")
    
    # 2. Live 디스플레이 구동 (실시간 트리 갱신)
    try:
        command_prompt = (
            f"Target Workspace: `{workspace}` 에 대해 L1, L2 룰 및 스킬을 융합하세요.\n"
            f"이 정책을 읽고 실행할 타겟 AI 에이전트는 `{target_agent}` 입니다.\n"
            f"해당 에이전트가 완벽히 이해하고 동작할 수 있도록 Rule과 Skill 파일의 내용(Format)을 맞춤형으로 작성하되, 배포 경로는 반드시 표준 규격(.agents/rules/, .agents/skills/)을 엄격히 준수하여 기획하세요."
        )
        
        # 스피너 애니메이션 상태 관리
        import itertools
        spinner_frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        spinner = itertools.cycle(spinner_frames)
        active_agent_id = None
        is_live_paused = False
        
        async def spinner_task():
            """백그라운드에서 현재 활성화된 에이전트의 트리 노드 스피너를 애니메이션 처리합니다."""
            while True:
                if active_agent_id and not is_live_paused and active_agent_id in nodes:
                    idx = [k for k, _ in agents_info].index(active_agent_id)
                    frame = next(spinner)
                    nodes[active_agent_id].label = f"[bold cyan]{frame} {agents_info[idx][1]} (진행중...)[/bold cyan]"
                await asyncio.sleep(0.1)

        # 애니메이션 태스크 시작
        bg_task = asyncio.create_task(spinner_task())
        
        with Live(main_tree, refresh_per_second=10, console=console) as live:
            async for event in pipeline.run(command_prompt=command_prompt, session_id=session_id):
                
                # A. 커스텀 상태(Phase/Tool) 이벤트 처리 (서브트리 갱신)
                if isinstance(event, dict) and "type" in event:
                    e_type = event["type"]
                    agent_id = event.get("agent")
                    
                    if e_type == "phase_start" and agent_id in nodes:
                        active_agent_id = agent_id # 애니메이션 타겟 설정
                        if "message" in event:
                            nodes[agent_id].add(f"[cyan]ℹ️ {event['message']}[/cyan]")
                            
                    elif e_type == "tool_call" and agent_id in nodes:
                        nodes[agent_id].add(f"[yellow]🔧 도구 호출: {event.get('tool_name')}[/yellow]")
                        
                    elif e_type == "phase_end" and agent_id in nodes:
                        if active_agent_id == agent_id:
                            active_agent_id = None # 애니메이션 중지
                        idx = [k for k, _ in agents_info].index(agent_id)
                        status_color = "green" if event.get("status") == "success" else "red"
                        icon = "✅" if event.get("status") == "success" else "❌"
                        nodes[agent_id].label = f"[bold {status_color}]{icon} {agents_info[idx][1]} (완료)[/bold {status_color}]"

                # B. HITL 승인 대기 / 사용자 입력창 이벤트 처리
                elif isinstance(event, dict) and event.get("status") in ["pending_approval", "pending_final_approval"]:
                    is_live_paused = True
                    live.stop() # UI 겹침 방지를 위해 렌더링 일시 중단
                    
                    is_final_approval = event.get("status") == "pending_final_approval"
                    
                    if is_final_approval:
                        console.print("\n[bold yellow]🔔 [최종 배포 승인 대기] 완벽한 산출물입니다. 배포를 직접 승인하시겠습니까?[/bold yellow]")
                    else:
                        console.print("\n[bold yellow]🔔 [HITL 승인 대기] 파괴적 변경이나 충돌이 감지되었습니다.[/bold yellow]")
                        
                    console.print("  ▶ 배포 승인 및 진행: [bold green]Y[/bold green] (또는 Enter)")
                    console.print("  ▶ 단순 배포 취소(반려): [bold red]N[/bold red]")
                    console.print("  ▶ 기획 재요청(피드백): [bold cyan]요구사항을 직접 타이핑하세요 (예: '로그 포맷 바꿔줘')[/bold cyan]")
                    
                    session = PromptSession()
                    user_input = await session.prompt_async('📝 피드백 또는 승인 입력 ❯ ')
                    user_input = user_input.strip()
                    
                    if user_input.lower() in ['y', 'yes', '승인', '']:
                        console.print("\n[bold green]✅ 승인 완료. 파이프라인을 계속 진행합니다.[/bold green]\n")
                        await pipeline.resume(session_id, {"approved": True})
                    elif user_input.lower() in ['n', 'no', '반려', '거절']:
                        console.print("\n[bold red]❌ 승인 거절. 파이프라인을 단순 반려합니다.[/bold red]\n")
                        await pipeline.resume(session_id, {"approved": False, "feedback": "관리자가 파이프라인 실행을 거절했습니다."})
                    else:
                        console.print(f"\n[bold magenta]💬 피드백 전달 완료. 에이전트 재기획 지시: '{user_input}'[/bold magenta]\n")
                        await pipeline.resume(session_id, {"approved": False, "feedback": user_input})
                    
                    is_live_paused = False
                    live.start() # 입력 완료 후 렌더링 재개

                # C. 상태 객체가 아닌 일반 텍스트 스트리밍은 패스 (Tree 구조 유지 위함)
                elif getattr(event, "content", None) and getattr(event.content, "parts", None):
                    pass

        bg_task.cancel() # 파이프라인 모두 종료 시 애니메이션 태스크 정리
        console.print("\n[bold green]🎉 모든 파이프라인 작업이 성공적으로 종료되었습니다![/bold green]")
        
    except Exception as e:
        console.print_exception(show_locals=False)
        console.print(f"\n[bold red]❌ 파이프라인 실행 중 오류가 발생했습니다: {e}[/bold red]")

@app.command
def sync(workspace: str = None, agent: str = "antigravity"):
    """
    사내 BookStack에 정의된 L1/L2 정책을 로컬 환경에 병합하고 배포합니다.
    
    Args:
        workspace: 동기화할 타겟 프로젝트 ID. 누락 시 대화형 자동완성 프롬프트가 실행됩니다.
        agent: 정책을 소비할 대상 AI 에이전트 이름 (기본값: antigravity)
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

    # 비동기 이벤트 루프 실행 시 agent 인자 전달
    asyncio.run(_run_pipeline(workspace, agent))

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
