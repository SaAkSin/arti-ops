import os
import asyncio
from prompt_toolkit.application import Application
from prompt_toolkit.layout.containers import HSplit, VSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets import Frame

async def run_list_viewer(plan_lookup, base_dir):
    """
    plan_lookup: { "rel_path": "Create" | "Update" }
    base_dir: .agents 디렉토리 경로
    """
    
    # 데이터 수집
    items = [] # (display_text, file_path)
    
    rules_dir = os.path.join(base_dir, "rules")
    if os.path.exists(rules_dir):
        items.append(("● Rules:", None))
        for filename in sorted(os.listdir(rules_dir)):
            if filename.endswith(".md"):
                rel_path = f".agents/rules/{filename}"
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
            items.append(("", None)) # 공백
        items.append(("◆ Skills:", None))
        for dirname in sorted(os.listdir(skills_dir)):
            skill_path = os.path.join(skills_dir, dirname)
            if os.path.isdir(skill_path):
                skill_file = os.path.join(skill_path, "SKILL.md")
                if os.path.exists(skill_file):
                    rel_path = f".agents/skills/{dirname}/SKILL.md"
                    if action := plan_lookup.get(rel_path):
                        if action == "Create": badge = "! "
                        elif action == "Update": badge = "* "
                        elif action == "Match": badge = "  "
                    display_text = f"  {badge}{dirname} (/SKILL.md)"
                    items.append((display_text, skill_file))
                else:
                    items.append((f"  {dirname} (SKILL.md 누락)", None))

    if not items:
        # 비어있으면 그냥 종료
        return

    # 상태 관리
    current_index = 0
    
    # 처음에 포커스 가능한 아이템 찾기
    for i, (_, path) in enumerate(items):
        if path:
            current_index = i
            break

    # UI 컴포넌트
    left_text_control = FormattedTextControl()
    right_text_control = FormattedTextControl(text="미리보기 화면입니다.\n좌측 목록에서 'Space'를 눌러 파일 내용을 확인하세요.")
    
    def update_left_pane():
        formatted_text = []
        for i, (text, path) in enumerate(items):
            if i == current_index and path:
                formatted_text.append(("class:selected", f"> {text}\n"))
            elif path:
                formatted_text.append(("", f"  {text}\n"))
            else:
                formatted_text.append(("class:header", f"{text}\n"))
        left_text_control.text = formatted_text
        
    update_left_pane()
    
    left_window = Window(content=left_text_control, wrap_lines=False, width=40)
    right_window = Window(content=right_text_control, wrap_lines=True)

    body = VSplit([
        Frame(left_window, title="로컬 파일 목록"),
        Frame(right_window, title="파일 미리보기")
    ])

    toolbar = Window(
        height=1,
        content=FormattedTextControl(
            text=" [↑/↓: 이동 | Space: 미리보기 | q / Esc / Enter: 닫기]"
        ),
        style="class:bottom-toolbar"
    )

    root_container = HSplit([body, toolbar])
    layout = Layout(root_container)

    kb = KeyBindings()

    @kb.add("q")
    @kb.add("escape")
    @kb.add("enter")
    def _(event):
        event.app.exit()

    @kb.add("up")
    def _(event):
        nonlocal current_index
        next_idx = current_index - 1
        while next_idx >= 0:
            if items[next_idx][1]: # path가 있으면 포커스 가능
                current_index = next_idx
                update_left_pane()
                break
            next_idx -= 1

    @kb.add("down")
    def _(event):
        nonlocal current_index
        next_idx = current_index + 1
        while next_idx < len(items):
            if items[next_idx][1]:
                current_index = next_idx
                update_left_pane()
                break
            next_idx += 1

    @kb.add("space")
    def _(event):
        _, path = items[current_index]
        if path and os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                right_text_control.text = content
            except Exception as e:
                right_text_control.text = f"파일을 읽는 중 오류가 발생했습니다: {e}"

    style = Style([
        ('bottom-toolbar', 'bg:#333333 #ffffff'),
        ('selected', 'bg:#00aa00 #ffffff bold'),
        ('header', 'bold #00ffff'),
    ])

    app = Application(
        layout=layout,
        key_bindings=kb,
        style=style,
        full_screen=True
    )

    await app.run_async()
