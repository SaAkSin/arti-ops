import os
import sys
import asyncio
import logging
from dotenv import load_dotenv

from cyclopts import App as CycloptsApp
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.tree import Tree
from rich.live import Live

from prompt_toolkit import PromptSession
from prompt_toolkit.shortcuts import clear
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.styles import Style

from ..core.pipeline import ArtiOpsPipeline

logger = logging.getLogger(__name__)

app = CycloptsApp(name="arti-ops", help="로컬 컨텍스트 기반 AgentOps CLI")
console = Console()

# 하단 프롬프트바 스타일 지정
pt_style = Style.from_dict({
    'bottom-toolbar': 'bg:#333333 #ffffff',
})

async def run_interactive_loop(workspace: str, target_agent: str):
    pipeline = ArtiOpsPipeline(target_project_id=workspace)
    session_id = f"sess_{workspace}_{target_agent}"
    
    # 1. 화면 정리 및 환영 메시지
    clear()
    console.print(Panel(
        f"[bold green]🚀 Target Workspace: '{workspace}' / Agent: '{target_agent}'[/bold green]\n"
        "[dim]명령어가 실행된 현재 디렉토리와 BookStack 정책을 분석하여 AI 스킬/룰을 자동 생성합니다.\n"
        "종료하려면 프롬프트에서 'q'를 입력하거나 Ctrl+C를 누르세요.[/dim]",
        title="arti-ops v0.5.0", border_style="blue"
    ))

    session = PromptSession(
        bottom_toolbar=lambda: " [q: 즉시 종료 / r: 세션 초기화 / Ctrl+C: 취소] 지시사항을 자연어로 입력하세요.",
        style=pt_style
    )

    while True:
        try:
            # 2. 하단 프롬프트 입력 대기
            with patch_stdout():
                user_input = await session.prompt_async("\n📝 프롬프트 지시 ❯ ")
                
            user_input = user_input.strip()
            
            # Kill-switch (즉시 종료)
            if user_input.lower() in ['q', 'quit', 'exit']:
                console.print("\n[bold red]👋 프로그램을 즉시 종료합니다.[/bold red]")
                sys.exit(0)
            
            # Session DB Cache Reset (캐시 초기화)
            if user_input.lower() in ['r', 'reset']:
                db_path = os.path.join(os.path.expanduser("~"), ".arti-ops", workspace, "sessions.db")
                if os.path.exists(db_path):
                    try:
                        os.remove(db_path)
                    except Exception as e:
                        logger.error(f"Failed to remove db: {e}")
                
                # 파이프라인 및 세션 서비스 즉시 재생성
                pipeline = ArtiOpsPipeline(target_project_id=workspace)
                console.print("\n[bold yellow]🔄 sessions.db 캐시가 초기화되었습니다. 완전히 백지 상태에서 새로 시작합니다![/bold yellow]")
                continue
                
            if not user_input:
                continue

            console.print(f"\n[cyan]▶ 사용자 지시:[/cyan] {user_input}\n")
            
            command_prompt = (
                f"사용자 지시: \"{user_input}\"\n\n"
                f"Target Workspace: `{workspace}`\n"
                f"타겟 에이전트: `{target_agent}`\n"
                f"위 지시를 바탕으로 로컬 현황과 BookStack 정책을 융합하여 새로운 룰/스킬을 생성하세요."
            )

            # 3. 라이브 상태 트리 준비
            main_tree = Tree(f"🔄 파이프라인 진행 상태")
            nodes = {}
            agents_info = [
                ("context_profiler", "Context Profiler"), 
                ("skill_architect", "Skill Architect"), 
                ("critical_verifier", "Critical Verifier"), 
                ("deployment_executor", "Deployment Executor")
            ]
            
            active_subnodes = {} # agent_id: set of (node_obj, original_text, color)
            for key, name in agents_info:
                nodes[key] = main_tree.add(f"[{'dim' if key != 'context_profiler' else 'bold'}]{name}[/]")
                # 초기 상태는 무조건 하위 노드로 대기중 한 줄만 표시
                wait_node = nodes[key].add("[dim]대기중[/dim]")
                active_subnodes[key] = {(wait_node, "대기중", "dim")}

            active_agents = set()
            SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

            def add_subnode(agent_id, text, color):
                if agent_id not in active_subnodes:
                    active_subnodes[agent_id] = set()
                new_node = nodes[agent_id].add(f"[{color}]{text}[/{color}]")
                active_subnodes[agent_id].add((new_node, text, color))

            def finish_subnode(agent_id, target_text, success=True):
                if agent_id in active_subnodes:
                    for obj in list(active_subnodes[agent_id]):
                        node, text, color = obj
                        if text == target_text:
                            active_subnodes[agent_id].remove(obj)
                            if success:
                                node.label = f"[dim {color}]{text}[/dim {color}]"
                            else:
                                node.label = f"[bold red]{text} (실패)[/bold red]"
                            break

            async def tree_animator():
                frame_idx = 0
                try:
                    while True:
                        for agent_id, sub_set in list(active_subnodes.items()):
                            for (node, text, color) in sub_set:
                                if text != "대기중":
                                    node.label = f"[{color}]{SPINNER_FRAMES[frame_idx]} {text}[/{color}]"
                        frame_idx = (frame_idx + 1) % len(SPINNER_FRAMES)
                        await asyncio.sleep(0.1)
                except asyncio.CancelledError:
                    pass

            # 4. 파이프라인 실행
            with Live(main_tree, refresh_per_second=10, console=console) as live:
                animator_task = asyncio.create_task(tree_animator())
                try:
                    async for event in pipeline.run(command_prompt=command_prompt, session_id=session_id):
                        
                        if isinstance(event, dict):
                            e_type = event.get("type")
                            status = event.get("status")
                            agent_id = event.get("agent")
                            
                            if e_type == "phase_start" and agent_id in nodes:
                                # 해당 에이전트 시작 시 하위 노드를 싹 비우고 활성화
                                nodes[agent_id].children.clear()
                                active_subnodes[agent_id] = set()
                                
                                active_agents.add(agent_id)
                                idx = [k for k, _ in agents_info].index(agent_id)
                                nodes[agent_id].label = f"[bold cyan]{agents_info[idx][1]}[/bold cyan]"
                                
                                if "message" in event:
                                    add_subnode(agent_id, event['message'], "cyan")
                                else:
                                    add_subnode(agent_id, "진행중...", "cyan")
                                    
                            elif e_type == "tool_call" and agent_id in nodes:
                                tool_name = event.get('tool_name')
                                add_subnode(agent_id, f"도구 실행: {tool_name}", "yellow")
                                
                            elif e_type == "subnode_add" and agent_id in nodes:
                                msg = event.get('message')
                                color = event.get('color', 'cyan')
                                add_subnode(agent_id, msg, color)
                                
                            elif e_type == "phase_end" and agent_id in nodes:
                                # 현재 돌고있는 모든 서브노드 완료 처리
                                if agent_id in active_subnodes:
                                    for obj in list(active_subnodes[agent_id]):
                                        node, text, color = obj
                                        finish_subnode(agent_id, text, success=(event.get("status") == "success"))
                                
                                if agent_id in active_agents:
                                    active_agents.remove(agent_id)
                                    
                                idx = [k for k, _ in agents_info].index(agent_id)
                                color = "green" if event.get("status") == "success" else "red"
                                state_str = "(완료)" if event.get("status") == "success" else "(실패)"
                                nodes[agent_id].label = f"[bold {color}]{agents_info[idx][1]}[/bold {color}]"
                                nodes[agent_id].add(f"[bold {color}]{state_str}[/bold {color}]")

                            # 5. 사전 검토 보고서 출력 및 판단 루프 (HITL)
                            elif status == "pending_final_approval":
                                live.stop() # 화면 깨짐 방지를 위해 트리 렌더링 일시 중지
                                
                                console.print("\n")
                                console.print(Panel(Markdown(event.get("report", "내용 없음")), title="📄 [최종 반영 검토 보고서]", border_style="yellow"))
                                console.print("[bold yellow]🔔 위 산출물을 확인하고 승인(Y) 하거나 수정 지시를 입력하세요.[/bold yellow]")
                                
                                while True:
                                    with patch_stdout():
                                        sub_input = await session.prompt_async("📝 승인(Y) / 반려(N) / 수정 요청 ❯ ")
                                    sub_input = sub_input.strip()
                                    
                                    if sub_input.lower() in ['q', 'quit']:
                                        animator_task.cancel()
                                        console.print("\n[bold red]👋 프로그램을 즉시 종료합니다.[/bold red]")
                                        sys.exit(0)
                                    elif sub_input.lower() in ['y', 'yes', '승인', 'ㅇㅇ', '']:
                                        console.print("\n[bold green]✅ 승인 완료. 로컬 배포 및 GWS 요약 전송을 시작합니다.[/bold green]")
                                        await pipeline.resume(session_id, {"approved": True})
                                        break
                                    elif sub_input.lower() in ['n', 'no', '반려', '거절', '취소']:
                                        console.print("\n[bold red]❌ 승인 거절. 초기 프롬프트로 돌아갑니다.[/bold red]")
                                        await pipeline.resume(session_id, {"approved": False, "feedback": "사용자가 반려했습니다."})
                                        break
                                    else:
                                        console.print(f"\n[bold magenta]💬 피드백 전달 완료. 요구사항을 반영하여 재기획합니다...[/bold magenta]")
                                        # 트리 상태 초기화 후 재가동
                                        for key, name in agents_info:
                                            nodes[key].label = f"[dim]{name}[/dim]"
                                            nodes[key].children.clear()
                                            wait_node = nodes[key].add("[dim]대기중[/dim]")
                                            active_subnodes[key] = {(wait_node, "대기중", "dim")}
                                        await pipeline.resume(session_id, {"approved": False, "feedback": sub_input})
                                        break
                                
                                live.start() # 트리 렌더링 재개
                finally:
                    animator_task.cancel()

            console.print("\n[bold green]🎉 요청하신 파이프라인 작업이 완료되었습니다. 추가 지시를 입력하세요.[/bold green]")

        except KeyboardInterrupt:
            console.print("\n[bold red]👋 사용자에 의해 강제 종료되었습니다 (Ctrl+C).[/bold red]")
            sys.exit(0)
        except EOFError:
            sys.exit(0)
        except Exception as e:
            console.print_exception(show_locals=False)
            console.print(f"\n[bold red]❌ 에러 발생: {e}[/bold red]")


@app.default
def main_cli(workspace: str = None, agent: str = "antigravity"):
    """
    현재 경로와 BookStack 정책을 참조하여 에이전트 환경을 대화형으로 생성합니다.
    """
    if not workspace:
        # 미입력 시 현재 명령어가 실행된 경로의 폴더명 추출
        workspace = os.path.basename(os.path.abspath(os.getcwd()))
        
    asyncio.run(run_interactive_loop(workspace, agent))

def main():
    load_dotenv()
    os.makedirs("logs", exist_ok=True)
    logging.basicConfig(
        filename="logs/arti-ops-cli.log",
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    app()

if __name__ == "__main__":
    main()
