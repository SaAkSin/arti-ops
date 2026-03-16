import os
import asyncio
from prompt_toolkit.application import Application
from prompt_toolkit.layout.containers import HSplit, VSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.filters import Condition, to_filter
from prompt_toolkit.shortcuts import checkboxlist_dialog
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets import Frame, TextArea


async def run_list_viewer(plan_lookup, base_dir, full_plan=None, bookstack=None, upsert_style=None):
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

    if not items:
        # 비어있으면 그냥 종료
        return

    # 상태 관리
    current_index = 0
    current_focus = "left"   # "left" or "right"
    is_edit_mode = False      # 편집 모드 여부
    is_dirty = False          # 미저장 변경 여부
    active_file_path = None   # 현재 우측 패널에 열린 파일 경로

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
        if is_edit_mode:
            toolbar_text_control.text = (
                " [Ctrl+S: 저장 | Esc: 편집 취소 | 내용 자유 수정 가능]"
            )
        elif current_focus == "right":
            toolbar_text_control.text = (
                f" [e: 편집 모드 | ↑/↓: 텍스트 스크롤 | Tab: 뷰 전환{upsert_hint} | q/Esc/Enter: 닫기]"
            )
        else:
            toolbar_text_control.text = (
                f" [↑/↓: 이동 | Space: 미리보기 | Tab: 뷰 전환{upsert_hint} | q/Esc/Enter: 닫기]"
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

    # ─── 종료: READ 모드에서만 동작 ───
    @kb.add("q", filter=Condition(lambda: not is_edit_mode))
    @kb.add("enter", filter=Condition(lambda: not is_edit_mode))
    def _(event):
        try:
            event.app.exit()
        except Exception:
            pass

    # ─── Esc: EDIT 모드이면 편집 취소, READ 모드이면 뷰어 종료 ───
    @kb.add("escape")
    def _(event):
        nonlocal is_edit_mode, is_dirty
        if is_edit_mode:
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

    # ─── Tab: 좌/우 포커스 전환 ───
    @kb.add("tab")
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

    # ─── Space: 파일 미리보기 로드 ───
    @kb.add("space", filter=Condition(lambda: not is_edit_mode))
    def _(event):
        nonlocal active_file_path
        _, path = items[current_index]
        if path and os.path.exists(path):
            active_file_path = path
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                right_text_area.text = content
            except Exception as e:
                right_text_area.text = f"파일을 읽는 중 오류가 발생했습니다: {e}"

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

    # l/u 다이얼로그 색상 일치: 두 구역 모두 터미널 기본 배경을 사용
    viewer_style = Style([
        ('bottom-toolbar', 'bg:#333333 #ffffff'),
        ('selected',       'bg:#00aa00 #ffffff bold'),
        ('header',         'bold #00ffff'),
    ])

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
