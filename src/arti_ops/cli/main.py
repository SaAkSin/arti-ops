import os
import sys
import asyncio
import logging
import sqlite3
import shutil
import httpx
from pathlib import Path
from typing import Optional

from cyclopts import App as CycloptsApp
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.tree import Tree
from rich.live import Live

from prompt_toolkit import PromptSession
from prompt_toolkit.shortcuts import clear, checkboxlist_dialog, yes_no_dialog
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.styles import Style
from prompt_toolkit.formatted_text import HTML

from ..core.pipeline import ArtiOpsPipeline
from ..tools.bookstack import BookStackToolset
from .list_viewer import run_list_viewer
from arti_ops.config import Configurator

logger = logging.getLogger(__name__)

app = CycloptsApp(name="arti-ops", help="로컬 컨텍스트 기반 AgentOps CLI")
console = Console()

# 하단 프롬프트바 및 다이얼로그 스타일 지정 (기본 터미널 테마와 유사하게 배색)
pt_style = Style.from_dict({
    'bottom-toolbar': 'bg:#333333 #ffffff',
    'dialog': 'bg:#2b2b2b',
    'dialog frame.label': 'bg:#2b2b2b #00ffff bold',
    'dialog.body': 'bg:#2b2b2b #dddddd',
    'dialog shadow': 'bg:#1a1a1a',
    'checkbox': '#00ff00',
    'checkbox-checked': '#00ff00 bold',
    'button': 'bg:#444444 #ffffff',
    'button.focused': 'bg:#00aa00 #ffffff bold',
})

async def handle_chat_query(user_input: str, workspace: str, console):
    api_key = Configurator.get_instance().get("GEMINI_API_KEY")
    model_name = Configurator.get_instance().get("GEMINI_MODEL_FLASH", "gemini-2.5-flash")
    if not api_key:
        console.print("[red]GEMINI_API_KEY가 설정되어 있지 않습니다.[/red]")
        return
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
    system_instruction = f"당신은 arti-ops CLI의 친절한 보조 AI 어시스턴트입니다.\n현재 사용자의 워크스페이스는 '{workspace}' 이며, 시스템이나 요구사항에 대한 질문에 간결하고 도움되는 답변을 한국어로 제공하세요."
    payload = {
        "system_instruction": {
            "parts": [{"text": system_instruction}]
        },
        "contents": [{"parts": [{"text": user_input}]}]
    }
    
    try:
        with console.status("[cyan]AI 응답 생성 중...[/cyan]", spinner="dots"):
            async with httpx.AsyncClient() as client:
                res = await client.post(url, json=payload, timeout=30.0)
                res.raise_for_status()
                data = res.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
        
        console.print(Panel(Markdown(text), title="💬 [bold cyan]Agent Assistant[/bold cyan]", border_style="cyan"))
    except Exception as e:
        console.print(f"[red]답변 생성 중 오류가 발생했습니다: {e}[/red]")

async def run_interactive_loop(workspace: str, target_agent: str):
    pipeline = ArtiOpsPipeline(target_project_id=workspace)
    session_id = f"sess_{workspace}_{target_agent}"
    
    # 1. 화면 정리 및 환영 메시지
    clear()
    console.print(Panel(
        f"[bold green]▶ Target Workspace: '{workspace}' / Agent: '{target_agent}'[/bold green]\n"
        "[dim]명령어가 실행된 현재 디렉토리와 BookStack 정책을 분석하여 AI 스킬/룰을 자동 생성합니다.\n"
        "종료하려면 프롬프트에서 'q'를 입력하거나 Ctrl+C를 누르세요.[/dim]",
        title="arti-ops v0.5.1", border_style="blue"
    ))

    def get_bottom_toolbar():
        if getattr(session, 'is_hitl', False):
            return HTML(' [<style fg="#888888"><i>s &lt;내용&gt;: 파이프라인 시작</i></style> | q: 종료 | <style fg="#888888"><i>r: 재시작</i></style> | <style fg="#888888"><i>u: 배포</i></style> | <style fg="#888888"><i>l: 파일 현황</i></style> | <style fg="#888888"><i>기타: 일반 AI 질의응답</i></style>]')
        return " [s <내용>: 파이프라인 시작 | q: 종료 | r: 재시작 | u: 배포 | l: 파일 현황 | 기타: 일반 AI 질의응답]"

    session = PromptSession(
        bottom_toolbar=get_bottom_toolbar,
        style=pt_style
    )
    session.is_hitl = False

    while True:
        try:
            # 2. 하단 프롬프트 입력 대기
            with patch_stdout():
                user_input = await session.prompt_async("\n■ 프롬프트 지시 ❯ ")
                
            user_input = user_input.strip()
            
            # Kill-switch (즉시 종료)
            if user_input.lower() in ['q', 'quit', 'exit']:
                console.print("\n[bold red]■ 프로그램을 즉시 종료합니다.[/bold red]")
                sys.exit(0)
            
            # Session DB Cache Reset (캐시 초기화)
            if user_input.lower() in ['r', 'reset']:
                db_path = os.path.expanduser("~/.arti-ops/arti_ops_session.db")
                if os.path.exists(db_path):
                    try:
                        conn = sqlite3.connect(db_path)
                        cursor = conn.cursor()
                        # cascade가 동작하지 않을 수 있으므로 events 테이블에서 먼저 삭제
                        cursor.execute("DELETE FROM events WHERE session_id LIKE ?", (f"%{workspace}%",))
                        # id 컬럼에 workspace(session_id 생성 규칙 참고)가 포함된 모든 세션 삭제
                        cursor.execute("DELETE FROM sessions WHERE id LIKE ?", (f"%{workspace}%",))
                        conn.commit()
                        conn.close()
                    except Exception as e:
                        logger.error(f"Failed to reset session in DB: {e}")
                
                # 파이프라인 및 세션 서비스 즉시 재생성
                pipeline = ArtiOpsPipeline(target_project_id=workspace)
                console.print("\n[bold yellow]🔄 sessions.db 캐시가 초기화되었습니다. 완전히 백지 상태에서 새로 시작합니다![/bold yellow]")
                continue
                
            # BookStack Upsert 동기화
            if user_input.lower() in ['u', 'upsert']:
                bookstack = BookStackToolset()
                with console.status("[cyan]BookStack 위키와 로컬 현황을 비교 분석 중입니다...[/cyan]", spinner="dots"):
                    try:
                        plan = await bookstack.get_upsert_plan(workspace)
                    except ValueError as e:
                        plan = None
                        error_msg = str(e)
                
                # 책이 없어서 예외가 발생한 경우 자동 생성 제안 (u 커맨드 전용)
                if plan is None:
                    do_create = await asyncio.to_thread(
                        yes_no_dialog(
                            title="위키 책(Book) 자동 생성",
                            text=f"{error_msg}\n\n지금 자동으로 '{workspace}' 프로젝트를 위한 새 책과 구조(rules, skills)를 위키에 생성하시겠습니까?",
                            style=pt_style
                        ).run
                    )
                    
                    if do_create:
                        with console.status("[cyan]▶ 새 워크스페이스 구조를 BookStack에 생성하고 있습니다...[/cyan]", spinner="dots"):
                            try:
                                await bookstack.create_workspace_book(workspace)
                                console.print("\n[bold green]✔ 새 위키 구조가 생성되었습니다! 로컬 배포 플랜을 다시 계산합니다.[/bold green]")
                                plan = await bookstack.get_upsert_plan(workspace)
                            except Exception as ex:
                                console.print(f"\n[bold red]✖ 위키 자동 생성 실패: {ex}[/bold red]")
                                continue
                    else:
                        console.print("\n[dim]작업이 취소되었습니다.[/dim]")
                        continue
                        
                if not plan:
                    console.print("[yellow]▼ 동기화할 수 있는 로컬(L3) 에셋(규칙, 스킬)을 찾을 수 없거나 BookStack 챕터 구조에 문제가 있습니다.[/yellow]")
                    continue
                
                # 액션에 따른 심볼 매핑
                def get_symbol(action):
                    if action == "Create": return "!"
                    elif action == "Update": return "*"
                    elif action == "Match": return " "
                    return " "

                choices = []
                for item in plan:
                    display_text = f"[{get_symbol(item['action'])}] {item['rel_path']}"
                    
                    if item.get("type") == "skills":
                        skill_dir = os.path.join(os.getcwd(), os.path.dirname(item["rel_path"]))
                        if os.path.exists(skill_dir):
                            for root, dirs, files in os.walk(skill_dir):
                                for file in sorted(files):
                                    if file == "SKILL.md" or file.startswith(".") or file.endswith(".pyc"):
                                        continue
                                    
                                    sub_path = os.path.join(root, file)
                                    rel_sub = os.path.relpath(sub_path, skill_dir)
                                    display_text += f"\n      ↳ {rel_sub}"
                                    
                    choices.append((item, display_text))
                
                selected_plan = await asyncio.to_thread(
                    checkboxlist_dialog(
                        title="위키 연동 (BookStack Upsert)",
                        text="방향키(↑/↓)와 스페이스바(Space)로 배포할 항목을 선택하거나 해제하세요.\n[ ! : 신규 추가 | * : 위키와 로컬 내용 다름 (업데이트 대상) | 공백 : 완벽히 동일 (수정 불필요) ]",
                        values=choices,
                        style=pt_style
                    ).run
                )
                
                if not selected_plan:
                    console.print("\n[dim]배포가 취소되었습니다. 선택된 항목이 없습니다.[/dim]")
                    continue
                    
                with console.status(f"[bold green]▶ {len(selected_plan)}개의 항목을 대상 BookStack 워크스페이스에 배포합니다...[/bold green]", spinner="dots"):
                    await bookstack.execute_upsert(selected_plan)
                console.print("[bold cyan]✔ 로컬-위키 연동이 성공적으로 완료되었습니다![/bold cyan]")
                continue
                
            # Local Asset List 조회
            if user_input.lower() in ['l', 'list']:
                base_dir = os.path.join(os.getcwd(), ".agents")
                if not os.path.exists(base_dir):
                    console.print("\n[yellow]▼ 현재 로컬에 수집/배포된 룰이나 스킬이 없습니다. (.agents 폴더 없음)[/yellow]")
                    continue
                
                bookstack = BookStackToolset()
                with console.status("[cyan]BookStack 위키와 로컬 현황을 비교 분석 중입니다...[/cyan]", spinner="dots"):
                    try:
                        plan = await bookstack.get_upsert_plan(workspace)
                    except ValueError as e:
                        console.print(f"\n[bold yellow]⚠ {e}[/bold yellow]")
                        continue
                
                # 룩업 딕셔너리 생성 (rel_path: action)
                plan_lookup = {item["rel_path"]: item["action"] for item in plan}
                
                # 대화형 List Viewer 실행
                await run_list_viewer(plan_lookup, base_dir)
                
                console.print("\n[bold cyan]✔ 로컬 현황 조회를 완료했습니다.[/bold cyan]")
                continue
                
            if not user_input:
                continue

            # 일반 챗 쿼리인지 파이프라인 시작(s)인지 분기
            if not (user_input.lower().startswith("s ") or user_input.lower() == "s" or user_input.lower().startswith("start ") or user_input.lower() == "start"):
                await handle_chat_query(user_input, workspace, console)
                continue
                
            user_prompt = user_input[2:].strip() if user_input.lower().startswith("s ") else user_input[6:].strip()
            if user_input.lower() in ["s", "start"]:
                console.print(
                    "\n[dim]★ 작성 예시:[/dim]\n"
                    "[dim]  1) 시작[/dim]\n"
                    "[dim]  2) 에이전트가 PR 리뷰를 수행할 수 있도록 돕는 코드 분석 스킬(skill) 스크립트를 만들어줘.[/dim]"
                )
                with patch_stdout():
                    user_prompt = await session.prompt_async("■ 수행할 AI 파이프라인 작업을 구체적으로 입력하세요 ❯ ")
                    user_prompt = user_prompt.strip()
                    
                if user_prompt.lower() in ['q', 'quit']:
                    console.print("\n[bold red]■ 프로그램을 즉시 종료합니다.[/bold red]")
                    sys.exit(0)
                        
                if not user_prompt:
                    continue
                    
                if user_prompt.lower() in ['l', 'list', 'u', 'upsert', 'r', 'reset']:
                    console.print(f"\n[yellow]⚠ '{user_prompt}' 커맨드는 메인 프롬프트에서 단독으로 입력해주세요. 파이프라인 지시사항으로는 부적절합니다.[/yellow]")
                    continue

            if user_prompt in ['1', '시작']:
                user_prompt = "현재 로컬 프로젝트의 구조와 이미 정의된 위키 정책들을 전반적으로 분석하십시오. 만약 위키에 존재하는 핵심/범용 규정이 있지만 이 워크스페이스 로컬(`.agents`)에 아직 반영되지 않았다면, 현재 프로젝트의 성격과 환경에 맞게 내용을 변형·병합하여 최적화된 로컬 룰(Rule)이나 범용 스킬(Skill)로 작성해줘."

            console.print(f"\n[cyan]▶ 파이프라인 수행 지시:[/cyan] {user_prompt}\n")
            
            command_prompt = (
                f"사용자 지시: \"{user_prompt}\"\n\n"
                f"Target Workspace: `{workspace}`\n"
                f"타겟 에이전트: `{target_agent}`\n"
                f"위 지시를 바탕으로 로컬 현황과 BookStack 정책을 융합하여 새로운 룰/스킬을 생성하세요."
            )

            # 3. 라이브 상태 트리 준비
            main_tree = Tree(f"◎ 파이프라인 진행 상태")
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
                                console.print(Panel(Markdown(event.get("report", "내용 없음")), title="≡ [최종 반영 검토 보고서]", border_style="yellow"))
                                console.print("[bold yellow]❖ 위 산출물을 확인하고 승인(Y) 하거나 수정 지시를 입력하세요.[/bold yellow]")
                                
                                cancel_pipeline = False
                                while True:
                                    session.is_hitl = True
                                    with patch_stdout():
                                        sub_input = await session.prompt_async("■ 승인(Y) / 반려(N) / 취소(C) / 수정 요청 ❯ ")
                                    session.is_hitl = False
                                    sub_input = sub_input.strip()
                                    
                                    if sub_input.lower() in ['q', 'quit']:
                                        animator_task.cancel()
                                        console.print("\n[bold red]■ 프로그램을 즉시 종료합니다.[/bold red]")
                                        sys.exit(0)
                                    elif sub_input.lower() in ['y', 'yes', '승인', 'ㅇㅇ', '']:
                                        console.print("\n[bold green]✔ 승인 완료. 로컬 배포 및 GWS 요약 전송을 시작합니다.[/bold green]")
                                        await pipeline.resume(session_id, {"approved": True})
                                        break
                                    elif sub_input.lower() in ['n', 'no', '반려', '거절']:
                                        console.print("\n[bold red]X 승인 거절. 요구사항을 반영하여 재기획합니다.[/bold red]")
                                        await pipeline.resume(session_id, {"approved": False, "feedback": "사용자가 반려했습니다."})
                                        break
                                    elif sub_input.lower() in ['c', '취소', 'cancel']:
                                        console.print("\n[bold yellow]■ 파이프라인 수행을 취소하고 초기 프롬프트로 돌아갑니다.[/bold yellow]")
                                        cancel_pipeline = True
                                        # pipeline generator cleanup will be triggered when breaking out of async for
                                        break
                                    else:
                                        console.print(f"\n[bold magenta]▶ 피드백 전달 완료. 요구사항을 반영하여 재기획합니다...[/bold magenta]")
                                        # 트리 상태 초기화 후 재가동
                                        for key, name in agents_info:
                                            nodes[key].label = f"[dim]{name}[/dim]"
                                            nodes[key].children.clear()
                                            wait_node = nodes[key].add("[dim]대기중[/dim]")
                                            active_subnodes[key] = {(wait_node, "대기중", "dim")}
                                        await pipeline.resume(session_id, {"approved": False, "feedback": sub_input})
                                        break
                                
                                live.start() # 트리 렌더링 재개
                                if cancel_pipeline:
                                    break
                finally:
                    animator_task.cancel()

            console.print("\n[bold green]★ 요청하신 파이프라인 작업이 완료되었습니다. 추가 지시를 입력하세요.[/bold green]")

        except KeyboardInterrupt:
            console.print("\n[bold red]👋 사용자에 의해 강제 종료되었습니다 (Ctrl+C).[/bold red]")
            sys.exit(0)
        except EOFError:
            sys.exit(0)
        except Exception as e:
            console.print_exception(show_locals=False)
            console.print(f"\n[bold red]✖ 에러 발생: {e}[/bold red]")


@app.command
def setup():
    """
    arti-ops 를 전역적으로 사용하기 위한 글로벌 인증 정보를 설정하거나 재설정합니다.
    """
    console.print(Panel("[bold cyan]arti-ops 글로벌 인증 설정[/bold cyan]"))
    
    home_dir = Path.home() / ".arti-ops"
    home_dir.mkdir(parents=True, exist_ok=True)
    
    cred_file = home_dir / "credentials"
    if cred_file.exists():
        console.print("┣ [yellow]기존 인증 정보가 존재합니다. 새로 입력하여 덮어씁니다.[/yellow]")
        
    try:
        from prompt_toolkit import prompt
        gemini_key = prompt("┃ ❯ Gemini API KeY: ", is_password=True).strip()
        bs_url = prompt("┃ ❯ BookStack API URL (ex: https://wiki.ok.com/api): ").strip()
        bs_id = prompt("┃ ❯ BookStack Token ID: ").strip()
        bs_secret = prompt("┃ ❯ BookStack Token Secret (pwd): ", is_password=True).strip()
        use_gws = prompt("┃ ❯ USE GWS CLI(y/n)? [n]: ").strip().lower() == 'y'
        
        with open(cred_file, "w") as f:
            f.write("[default]\n")
            f.write(f"GEMINI_API_KEY={gemini_key}\n")
            f.write("GEMINI_MODEL_PRO=gemini-2.5-pro\n")
            f.write("GEMINI_MODEL_FLASH=gemini-2.5-flash\n")
            f.write(f"BOOKSTACK_API_URL={bs_url}\n")
            f.write(f"BOOKSTACK_TOKEN_ID={bs_id}\n")
            f.write(f"BOOKSTACK_TOKEN_SECRET={bs_secret}\n")
            f.write(f"USE_GWS_CLI={'true' if use_gws else 'false'}\n")
        console.print("┣ [green]글로벌 인증 저장 완료:[/green] ~/.arti-ops/credentials")
    except EOFError:
        console.print("┣ [yellow]설정이 취소되었습니다.[/yellow]")
    except KeyboardInterrupt:
        console.print("┣ [yellow]설정이 취소되었습니다.[/yellow]")

@app.command
def init():
    """
    arti-ops 를 전역적으로 사용하기 위한 글로벌(+로컬) 환경을 스캐폴딩(초기화)합니다.
    """
    console.print(Panel("[bold cyan]arti-ops 초기화 마법사[/bold cyan]"))
    
    # 1. 로컬 디렉토리 스캐폴딩
    Path(".agents/rules").mkdir(parents=True, exist_ok=True)
    Path(".agents/skills").mkdir(parents=True, exist_ok=True)
    console.print("┣ [green]로컬 폴더 생성 완료:[/green] .agents/rules, .agents/skills")
    
    # 2. 로컬 설정 (.artiops.toml) 작성
    local_conf = Path(".artiops.toml")
    if not local_conf.exists():
        current_dir = Path.cwd().name
        with open(local_conf, "w") as f:
            f.write(f'current_project_id = "{current_dir}"\n')
        console.print(f"┣ [green]로컬 식별자 생성 완료:[/green] .artiops.toml (project_id='{current_dir}')")
    
    # 3. 글로벌 설정 프롬프트
    home_dir = Path.home() / ".arti-ops"
    cred_file = home_dir / "credentials"
    if not cred_file.exists():
        console.print("┣ [dim]글로벌 인증 정보가 없습니다 (처음 1회만 입력).[/dim]")
        setup()
            
    console.print("┗ [bold green]모든 준비가 완료되었습니다! 이제 `arti-ops` 명령어를 사용하세요.[/bold green]")


@app.default
def main_cli(workspace: Optional[str] = None, agent: str = "antigravity"):
    """
    현재 경로와 BookStack 정책을 참조하여 에이전트 환경을 대화형으로 생성합니다.
    """
    # 글로벌 인증 정보 존재 여부 사전 검증 (Guard)
    cred_file = Path.home() / ".arti-ops" / "credentials"
    if not cred_file.exists():
        console.print(Panel(
            "[bold red]글로벌 인증 정보가 설정되지 않았습니다.[/bold red]\n\n"
            "arti-ops 를 사용하려면 먼저 글로벌 인증(Gemini API Key, BookStack 등)을 등록해야 합니다.\n"
            "아래 명령어를 실행하여 초기 설정을 완료하세요:\n\n"
            "  [bold cyan]$ arti-ops setup[/bold cyan]",
            title="⚠ 설정 필요", border_style="red"
        ))
        return

    config = Configurator.get_instance()
    
    if not workspace:
        workspace = config.project_id or os.path.basename(os.path.abspath(os.getcwd()))
        
    asyncio.run(run_interactive_loop(workspace, agent))

def main():
    log_dir = os.path.expanduser("~/.arti-ops/logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "arti-ops-cli.log")
    
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    app()

if __name__ == "__main__":
    main()
