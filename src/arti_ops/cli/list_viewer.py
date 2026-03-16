import os
import difflib
import asyncio
import subprocess
from prompt_toolkit.application import Application, get_app
from prompt_toolkit.layout.containers import HSplit, VSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.filters import Condition, to_filter
from prompt_toolkit.shortcuts import checkboxlist_dialog
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets import Frame, TextArea
from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part
from arti_ops.agents.globalizer import get_globalizer_agent


async def run_list_viewer(plan_lookup, base_dir, full_plan=None, bookstack=None, upsert_style=None, project_id=None):
    """
    plan_lookup: { "rel_path": "Create" | "Update" | "Match" }
    base_dir: .agents 디렉토리 경로
    """

    # 데이터 수집
    items = []  # (display_text, file_path)

    rules_dir = os.path.join(base_dir, "rules")
    if os.path.exists(rules_dir):
        items.append(("● Rules:", None))
        for filename in sorted(os.listdir(rules_dir)):
            if filename.endswith(".md"):
                rel_path = f".agents/rules/{filename}"
                badge = "  "
                if action := plan_lookup.get(rel_path):
                    if action == "Create": badge = "! "
                    elif action == "Update": badge = "* "
                    elif action == "Match": badge = "  "

                display_text = f"  {badge}{filename}"
                file_path = os.path.join(rules_dir, filename)
                items.append((display_text, file_path))

    skills_dir = os.path.join(base_dir, "skills")
    if os.path.exists(skills_dir):
        if items:
            items.append(("", None))  # 공백
        items.append(("◆ Skills:", None))
        for dirname in sorted(os.listdir(skills_dir)):
            skill_path = os.path.join(skills_dir, dirname)
            if os.path.isdir(skill_path):
                skill_file = os.path.join(skill_path, "SKILL.md")
                if os.path.exists(skill_file):
                    rel_path = f".agents/skills/{dirname}/SKILL.md"
                    badge = "  "
                    if action := plan_lookup.get(rel_path):
                        if action == "Create": badge = "! "
                        elif action == "Update": badge = "* "
                        elif action == "Match": badge = "  "
                    display_text = f"  {badge}{dirname} (SKILL.md)"
                    items.append((display_text, skill_file))

                    # 스크립트 등 부속 파일 탐색
                    for root, dirs, files in os.walk(skill_path):
                        for file in sorted(files):
                            if file == "SKILL.md" or file.startswith("."):
                                continue

                            sub_path = os.path.join(root, file)
                            rel_sub = os.path.relpath(sub_path, skill_path)
                            items.append((f"      ↳ {rel_sub}", sub_path))
                else:
                    items.append((f"  {dirname} (SKILL.md 누락)", None))

    # ─── Docs 섹션: PRD.md / SSD.md (L2/L3만 존재, L1 없음) ───
    project_root = os.path.dirname(base_dir)  # base_dir = .agents/ 의 부모
    docs_targets = ["PRD.md", "SSD.md"]
    docs_items = [(fname, os.path.join(project_root, fname))
                  for fname in docs_targets
                  if os.path.exists(os.path.join(project_root, fname))]
    if docs_items:
        if items:
            items.append(("", None))
        items.append(("■ Docs:", None))
        for fname, fpath in docs_items:
            items.append((f"  {fname}", fpath))

    if not items:
        # 비어있으면 그냥 종료
        return

    # 상태 관리
    current_index = 0
    current_focus = "left"   # "left" or "right"
    is_edit_mode = False      # 편집 모드 여부
    is_dirty = False          # 미저장 변경 여부
    active_file_path = None   # 현재 우측 패널에 열린 파일 경로
    is_l1_preview = False     # L1 변환 미리보기 표시 중인지 여부
    is_diff_view = False      # Diff 결과 표시 중인지 여부
    original_content = ""     # L1 미리보기 / Diff Esc 복원용 원본 내용

    # 처음에 포커스 가능한 아이템 찾기
    for i, (_, path) in enumerate(items):
        if path:
            current_index = i
            break

    # UI 컴포넌트
    left_text_control = FormattedTextControl()
    right_text_area = TextArea(
        text="미리보기 화면입니다.\n좌측 목록에서 'Space'를 눌러 파일 내용을 확인하세요.",
        read_only=True,
        scrollbar=True,
        wrap_lines=True,
    )

    def update_left_pane():
        """좌측 목록 배지를 plan_lookup 기준으로 다시 렌더링한다."""
        # 아이템 목록의 배지를 최신 plan_lookup 기준으로 재계산
        formatted_text = []
        item_idx = 0
        for i, (text, path) in enumerate(items):
            if i == current_index and path:
                formatted_text.append(("class:selected", f"> {text}\n"))
            elif path:
                formatted_text.append(("", f"  {text}\n"))
            else:
                formatted_text.append(("class:header", f"{text}\n"))
        left_text_control.text = formatted_text

    def rebuild_items_badges():
        """저장 후 items 목록의 display_text 배지를 plan_lookup에 맞게 갱신한다."""
        badge_map = {"Create": "! ", "Update": "* ", "Match": "  "}
        for i, (text, path) in enumerate(items):
            if path is None:
                continue
            # rules의 rel_path 계산
            if path.endswith(".md"):
                try:
                    # base_dir의 상위 디렉토리 기준 상대 경로 (예: .agents/rules/xxx.md)
                    rel = os.path.relpath(path, os.path.dirname(base_dir)).replace("\\", "/")
                except Exception:
                    continue
                action = plan_lookup.get(rel, "")
                badge = badge_map.get(action, "  ")
                # display_text 재조합: 기존 배지(2자리) 교체
                name_part = text.lstrip()   # "! foo.md" → "foo.md"
                if len(name_part) > 2 and name_part[1] == " ":
                    name_part = name_part[2:]  # "! " 제거
                items[i] = (f"  {badge}{name_part}", path)

    update_left_pane()

    toolbar_text_control = FormattedTextControl(
        text=" [↑/↓: 이동 | Space: 미리보기 | Tab: 뷰 전환 | q / Esc / Enter: 닫기]"
    )

    def update_toolbar():
        """현재 모드/포커스에 맞는 toolbar 힌트를 갱신한다."""
        upsert_hint = " | u: 위키 배포" if (full_plan and bookstack) else ""
        is_agents = active_file_path and ".agents" in active_file_path
        g_hint = " | g: L1 변환" if is_agents else ""
        d_hint = " | d: Diff비교" if bookstack else ""
        if is_edit_mode:
            toolbar_text_control.text = (
                " [Ctrl+S: 저장 | Esc: 편집 취소 | 내용 자유 수정 가능]"
            )
        elif is_l1_preview:
            toolbar_text_control.text = (
                " [L1 변환 미리보기 중 | Ctrl+C / ⌘+C: 클립보드 복사 | Esc: 원본 복원]"
            )
        elif is_diff_view:
            toolbar_text_control.text = (
                " [Diff 뷰 중 | Ctrl+C: 복사 | Esc: 원본 복원]"
            )
        elif current_focus == "right":
            toolbar_text_control.text = (
                f" [e: 편집{g_hint}{d_hint} | Ctrl+C: 복사 | ↑/↓: 스크롤 | Tab: 뷰 전환{upsert_hint} | q/Esc: 닫기]"
            )
        else:
            toolbar_text_control.text = (
                f" [↑/↓: 이동+미리보기 | Enter: 편집{g_hint}{d_hint} | Tab: 뷰 전환{upsert_hint} | q/Esc: 닫기]"
            )

    def get_right_panel_title():
        """우측 패널 Frame 타이틀을 동적으로 반환한다."""
        if is_edit_mode:
            dirty_mark = " [미저장 *]" if is_dirty else ""
            return f"▶ 파일 편집 중 ✏️{dirty_mark}"
        elif current_focus == "right":
            return "▶ 파일 미리보기 (포커스됨)"
        return "파일 미리보기"

    body = VSplit([
        Frame(
            Window(content=left_text_control, wrap_lines=False, width=40),
            title=lambda: "▶ 로컬 파일 목록 (포커스됨)" if current_focus == "left" else "로컬 파일 목록"
        ),
        Frame(right_text_area, title=get_right_panel_title)
    ])

    toolbar = Window(
        height=1,
        content=toolbar_text_control,
        style="class:bottom-toolbar"
    )

    root_container = HSplit([body, toolbar])
    layout = Layout(root_container)

    kb = KeyBindings()

    # ─── 더티 상태 감지 ───
    def on_text_changed(_):
        nonlocal is_dirty
        if is_edit_mode:
            is_dirty = True

    right_text_area.buffer.on_text_changed += on_text_changed

    # ─── 종료: READ 모드에서 q만 동작 (Enter는 편집 모드 진입으로 재정의) ───
    @kb.add("q", filter=Condition(lambda: not is_edit_mode))
    def _(event):
        try:
            event.app.exit()
        except Exception:
            pass

    # ─── Esc: L1 미리보기 복원 → EDIT 취소 → 뷰어 종료 순으로 처리 ───
    @kb.add("escape")
    def _(event):
        nonlocal is_edit_mode, is_dirty, is_l1_preview, is_diff_view
        if is_l1_preview or is_diff_view:
            # L1 미리보기 / Diff 뷰 중: 원본 복원
            right_text_area.text = original_content
            is_l1_preview = False
            is_diff_view = False
            update_toolbar()
        elif is_edit_mode:
            # 편집 취소: 원본 복원
            is_edit_mode = False
            is_dirty = False
            right_text_area.buffer.read_only = to_filter(True)
            if active_file_path and os.path.exists(active_file_path):
                with open(active_file_path, "r", encoding="utf-8") as f:
                    right_text_area.text = f.read()
            update_toolbar()
        else:
            # 뷰어 종료
            try:
                event.app.exit()
            except Exception:
                pass

    # ─── Tab: 좌/우 포커스 전환 (EDIT 모드에서는 차단) ───
    @kb.add("tab", filter=Condition(lambda: not is_edit_mode))
    def _(event):
        nonlocal current_focus
        if current_focus == "left":
            current_focus = "right"
        else:
            current_focus = "left"
        update_toolbar()

    # ─── 방향키: 좌측 탐색 또는 우측 스크롤 ───
    @kb.add("up")
    def _(event):
        nonlocal current_index
        if current_focus == "left":
            next_idx = current_index - 1
            while next_idx >= 0:
                if items[next_idx][1]:
                    current_index = next_idx
                    _load_preview()      # ─ 자동 미리보기
                    update_left_pane()
                    break
                next_idx -= 1
        elif current_focus == "right":
            right_text_area.buffer.cursor_up(count=event.arg)

    @kb.add("down")
    def _(event):
        nonlocal current_index
        if current_focus == "left":
            next_idx = current_index + 1
            while next_idx < len(items):
                if items[next_idx][1]:
                    current_index = next_idx
                    _load_preview()      # ─ 자동 미리보기
                    update_left_pane()
                    break
                next_idx += 1
        elif current_focus == "right":
            right_text_area.buffer.cursor_down(count=event.arg)

    @kb.add("pageup")
    def _(event):
        if current_focus == "right":
            right_text_area.buffer.cursor_up(count=15)

    @kb.add("pagedown")
    def _(event):
        if current_focus == "right":
            right_text_area.buffer.cursor_down(count=15)

    # ─── 좌/우 키: EDIT 모드가 아닐 때는 TextArea 기본 커서 이동을 차단 ───
    # TextArea는 항상 실제 포커스를 가지므로, 명시적으로 소비하지 않으면
    # current_focus == "left" 상태에서도 커서가 우측 패널에서 움직인다.
    @kb.add("left", filter=Condition(lambda: not is_edit_mode))
    @kb.add("right", filter=Condition(lambda: not is_edit_mode))
    def _(event):
        pass  # no-op으로 소비

    # ─── u: Upsert ↔ l 다시 진입하는 복귀 패턴 ───
    # asyncio.ensure_future 대신 app.exit 해서 다이얼로그를 같은 Application 실행에서 릹지 않게 함.
    @kb.add("u", filter=Condition(
        lambda: full_plan is not None and bookstack is not None and not is_edit_mode
    ))
    def trigger_upsert(event):
        """l 뷰어를 일시 종료 후 upsert 다이얼로그를 실행하고 발어 재진입한다."""
        event.app.exit(result="upsert_requested")

    # ─── _load_preview: 파일 로드 헬퍼 (자동 미리보기 및 Enter 진입에서 공유) ───
    def _load_preview():
        """items[current_index]의 파일을 우측 패널에 로드한다."""
        nonlocal active_file_path
        _, path = items[current_index]
        if path and os.path.exists(path):
            active_file_path = path
            try:
                with open(path, "r", encoding="utf-8") as f:
                    right_text_area.text = f.read()
            except Exception as e:
                right_text_area.text = f"파일을 읽는 중 오류: {e}"

    # ─── Enter (좌측): 파일 로드 + 즉시 EDIT 모드 진입 ───
    @kb.add("enter", filter=Condition(
        lambda: not is_edit_mode and current_focus == "left"
    ))
    def enter_to_edit(event):
        nonlocal current_focus, is_edit_mode
        _load_preview()
        if active_file_path is not None:  # 파일이 로드된 경우에만 편집 모드 진입
            current_focus = "right"
            is_edit_mode = True
            right_text_area.buffer.read_only = to_filter(False)
            update_toolbar()

    # ─── e: EDIT 모드 진입 (우측 포커스 + 파일이 열린 경우에 한정) ───
    @kb.add("e", filter=Condition(
        lambda: current_focus == "right"
            and active_file_path is not None
            and not is_edit_mode
    ))
    def enter_edit_mode(event):
        nonlocal is_edit_mode
        is_edit_mode = True
        right_text_area.buffer.read_only = to_filter(False)
        update_toolbar()

    # ─── Ctrl+S: 저장 (EDIT 모드에서만) ───
    @kb.add("c-s", filter=Condition(lambda: is_edit_mode))
    def save_file(event):
        nonlocal is_dirty
        if active_file_path:
            try:
                with open(active_file_path, "w", encoding="utf-8") as f:
                    f.write(right_text_area.text)
                is_dirty = False

                # 배지 갱신 로직:
                # - Create(!) → 유지: 위키에 없음은 변하지 않음
                # - Update(*) → 유지: 로컬만 수정해도 위키와 다름은 여전함
                # - Match(공백) → Update(*): 로컬이 바뀌었으므로 이제 위키와 다름
                rel = os.path.relpath(
                    active_file_path, os.path.dirname(base_dir)
                ).replace("\\", "/")
                if plan_lookup.get(rel) == "Match":
                    plan_lookup[rel] = "Update"

                rebuild_items_badges()
                update_left_pane()

            except Exception as e:
                right_text_area.text = right_text_area.text + f"\n\n[저장 오류: {e}]"

    # ─── g: L1 변환 미리보기 (.agents 파일에 한정, PRD/SSD 제외) ───
    @kb.add("g", filter=Condition(
        lambda: not is_edit_mode
            and active_file_path is not None
            and ".agents" in (active_file_path or "")
    ))
    def trigger_l1_convert(event):
        """g 키: 현재 파일을 L1 전역 정첵으로 변환하여 우측 패널에 표시한다."""
        asyncio.ensure_future(_do_l1_convert())

    async def _do_l1_convert():
        """ADK globalizer 에이전트로 L3 콘텐츠를 L1 전역 정책으로 일반화한다."""
        nonlocal is_l1_preview, original_content
        original_content = right_text_area.text
        right_text_area.text = "변환 중..."
        is_l1_preview = True

        # ── toolbar 스피너: |/-\\ 프레임을 0.12초 주기로 회전 ──
        frames = ["|", "/", "-", "\\"]
        spinner_running = True

        async def _spinner():
            i = 0
            while spinner_running:
                toolbar_text_control.text = (
                    f" [L1 변환 중 {frames[i % 4]}  |  Esc: 취소]"
                )
                i += 1
                try:
                    get_app().invalidate()  # 화면 강제 갱신 (스피너 애니메이션)
                except Exception:
                    pass
                await asyncio.sleep(0.12)

        spinner_task = asyncio.ensure_future(_spinner())
        try:
            runner = Runner(
                app_name="l1-globalizer",
                agent=get_globalizer_agent(),
                session_service=InMemorySessionService(),
                auto_create_session=True
            )
            parts = []
            async for event in runner.run_async(
                user_id="viewer",
                session_id="l1_convert",
                new_message=Content(role="user", parts=[
                    Part.from_text(text=f"다음 L3 콘텐츠를 L1 전역 정책으로 변환해주세요:\n\n{original_content}")
                ])
            ):
                if event.is_final_response():
                    parts = event.content.parts if event.content else []
            right_text_area.text = "\n".join(p.text for p in parts if hasattr(p, "text")) or "[변환 결과 없음]"
        except Exception as e:
            right_text_area.text = f"[변환 실패: {e}]\n\n{original_content}"
            is_l1_preview = False
        finally:
            spinner_running = False
            spinner_task.cancel()
        update_toolbar()

    # ─── d: L2(Workspace) Diff / D: L1(Global) Diff (.agents 파일 전용) ───
    _diff_filter = Condition(
        lambda: not is_edit_mode
            and active_file_path is not None
            and bookstack is not None
    )
    _diff_l1_filter = Condition(
        lambda: not is_edit_mode
            and active_file_path is not None
            and bookstack is not None
            and ".agents" in (active_file_path or "")
    )

    @kb.add("d", filter=_diff_filter)
    def trigger_diff_l2(event):
        """d 키: L2(Workspace) vs 로컬 diff."""
        asyncio.ensure_future(_do_diff("workspace"))

    @kb.add("D", filter=_diff_l1_filter)
    def trigger_diff_l1(event):
        """D 키: L1(Global) vs 로컬 diff (.agents 파일 전용)."""
        asyncio.ensure_future(_do_diff("global"))

    def _extract_page_section(wiki_md: str, file_path: str) -> str:
        """wiki_md(fetch_policies 결과)에서 현재 파일에 대응하는 섹션을 추출한다."""
        import re
        if "rules" in file_path:
            page_name = os.path.basename(file_path).replace(".md", "")
        elif "skills" in file_path:
            page_name = os.path.basename(os.path.dirname(file_path))
        else:
            # PRD.md / SSD.md 등 Docs 파일: 파일명으로 매칭
            page_name = os.path.basename(file_path).replace(".md", "")
        pattern = rf"### {re.escape(page_name)}[^\n]*\n(.*?)(?=\n###|\Z)"
        m = re.search(pattern, wiki_md, re.DOTALL)
        return m.group(1).strip() if m else f"(BookStack에서 '{page_name}' 페이지를 찾을 수 없음)"

    async def _do_diff(scope: str):
        """BookStack 정책과 로컬 파일을 difflib으로 비교해 우측 패널에 표시."""
        nonlocal is_diff_view, original_content

        original_content = right_text_area.text
        is_diff_view = True
        scope_label = "L1 Global" if scope == "global" else "L2 Workspace"
        right_text_area.text = f"BookStack({scope_label}) 와 비교 중..."
        update_toolbar()

        try:
            # project_id: workspace scope일 때 필수. run_list_viewer에서 전달받음
            pid = project_id if scope == "workspace" else None
            wiki_md = await bookstack.fetch_policies(
                scope_tag=scope,
                project_id=pid
            )
            wiki_section = _extract_page_section(wiki_md, active_file_path)
            local_lines = original_content.splitlines(keepends=True)
            wiki_lines = wiki_section.splitlines(keepends=True)
            diff_lines = list(difflib.unified_diff(
                wiki_lines,
                local_lines,
                fromfile=f"BookStack ({scope_label})",
                tofile="로컬 파일",
                lineterm=""
            ))
            result = "\n".join(diff_lines) if diff_lines else "차이 없음 — BookStack과 완전히 일치합니다."
            right_text_area.text = result
        except Exception as e:
            right_text_area.text = f"[Diff 실패: {e}]\n\n{original_content}"
            is_diff_view = False
        update_toolbar()

    # ─── Ctrl+C / CMD+C: 우측 패널 내용 클립보드 복사 (macOS pbcopy) ───
    @kb.add("c-c", filter=Condition(lambda: not is_edit_mode))
    @kb.add("c-@", filter=Condition(lambda: not is_edit_mode))  # macOS ⌘+C 바인딩
    def copy_to_clipboard(event):
        """READ/L1 미리보기 모드에서 Ctrl+C / ⌘+C 로 우측 패널 내용을 클립보드에 복사한다."""
        content = right_text_area.text
        if content:
            subprocess.run(["pbcopy"], input=content, text=True, check=False)

    # l/u 다이얼로그 색상 일치: 두 구역 모두 터미널 기본 배경을 사용
    viewer_style = Style([
        ('bottom-toolbar', 'bg:#333333 #ffffff'),
        ('selected',       'bg:#00aa00 #ffffff bold'),
        ('header',         'bold #00ffff'),
    ])

    # ─── 초기 자동 로드: 첫 유효 항목을 우측 패널에 자동 표시 ───
    _load_preview()

    # ─── Application 루프: upsert 후 런타임에 재진입 ───
    # Application 인스턴스는 재사용이 불가하므로 루프 내에서 매번 생성
    while True:
        app = Application(
            layout=layout,
            key_bindings=kb,
            style=viewer_style,
            full_screen=True
        )
        result = await app.run_async()

        # u 키로 요청된 경우: 다이얼로그 실행 후 배지 갱신 후 늉어로 복귀
        if result == "upsert_requested" and full_plan and bookstack:
            def get_symbol(action):
                return {"Create": "!", "Update": "*", "Match": " "}.get(action, " ")

            choices = []
            for item in full_plan:
                # Match(위키와 동일) 항목은 배포 대상이 아니므로 제외
                if item.get("action") == "Match":
                    continue
                display_text = f"[{get_symbol(item['action'])}] {item['rel_path']}"
                if item.get("type") == "skills":
                    skill_dir = os.path.join(os.getcwd(), os.path.dirname(item["rel_path"]))
                    if os.path.exists(skill_dir):
                        for root, _, files in os.walk(skill_dir):
                            for file in sorted(files):
                                if file == "SKILL.md" or file.startswith(".") or file.endswith(".pyc"):
                                    continue
                                sub_path = os.path.join(root, file)
                                rel_sub = os.path.relpath(sub_path, skill_dir)
                                display_text += f"\n      ↳ {rel_sub}"
                choices.append((item, display_text))

            # 다이얼로그를 Application 밖에서 (실행 중인 App 없음) 실행 → 스타일 정상 적용
            selected = await asyncio.to_thread(
                checkboxlist_dialog(
                    title="위키 연동 (BookStack Upsert)",
                    text=(
                        "방향키(↑/↓)와 스페이스바(Space)로 배포할 항목을 선택하세요.\n"
                        "[ ! : 신규 추가 | * : 위키와 로컈 내용 다름 (업데이트 대상) | 공백 : 컨텐츠 완전 동일 (수정 불필요) ]"
                    ),
                    values=choices,
                    style=upsert_style
                ).run
            )

            if selected:
                await bookstack.execute_upsert(selected)
                for item in selected:
                    plan_lookup[item["rel_path"]] = "Match"
                rebuild_items_badges()
                update_left_pane()

            # 선택함/안 함/취소 모두 누어로 복귀
            continue

        # q/Esc/Enter 등 일반 종료 → 루프 탈출
        break
