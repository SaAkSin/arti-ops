import argparse
import asyncio
import os
import logging
from dotenv import load_dotenv
from textual.app import App, ComposeResult
from textual.containers import Container, VerticalScroll
from textual.widgets import Header, Footer, Label, Static
from rich.markdown import Markdown

class ChatBubble(Static):
    """실시간으로 Markdown 텍스트를 파싱하여 보여주는 채팅 블록"""
    def __init__(self, role: str, initial_text: str=""):
        super().__init__()
        self.role = role
        self._text = initial_text
        self.content_widget = Static(Markdown(self._text), classes="chat_content")

    def compose(self) -> ComposeResult:
        if self.role.lower() == "system":
            yield Label(f"⚙️ {self.role}", classes="chat_role system_role")
        elif self.role.lower() == "user":
            yield Label(f"👤 {self.role}", classes="chat_role user_role")
        else:
            yield Label(f"🤖 {self.role}", classes="chat_role ai_role")
        yield self.content_widget

    def append_text(self, text: str):
        self._text += text
        self.content_widget.update(Markdown(self._text))

class ArtiOpsApp(App):
    """
    arti-ops TUI 애플리케이션
    Claude CLI 스타일의 모던한 마크다운 채팅 인터페이스를 제공합니다.
    """
    CSS = """
    Screen {
        background: $surface;
    }
    #chat_container {
        height: 1fr;
        padding: 1 2;
        overflow-y: scroll;
    }
    ChatBubble {
        margin-top: 1;
        margin-bottom: 1;
        background: $panel;
        padding: 1 2;
        border-left: thick $accent;
    }
    .chat_role {
        text-style: bold;
        margin-bottom: 1;
    }
    .system_role { color: $warning; }
    .user_role { color: $text; }
    .ai_role { color: $success; }
    .chat_content {
        margin-left: 2;
    }
    #status_bar {
        dock: bottom;
        height: 1;
        padding: 0 1;
        background: $accent;
        color: $text;
        text-style: bold;
    }
    """
    
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("ctrl+c", "quit", "Quit")
    ]

    def __init__(self, target_project: str):
        super().__init__()
        self.target_project = target_project
        self.chat_container = VerticalScroll(id="chat_container")
        self.status_bar = Label(f"🚀 Ready to sync: {self.target_project}", id="status_bar")
        self.current_ai_bubble = None
        
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield self.chat_container
        yield self.status_bar

    async def on_mount(self) -> None:
        self.title = "arti-ops v0.1.0"
        self.sub_title = "ADK Policy Sync Environment"
        
        sys_bubble = ChatBubble(role="System", initial_text="최신 정책 융합 및 배포 파이프라인 엔진을 가동합니다...")
        self.chat_container.mount(sys_bubble)
        
        # 시작 프롬프트를 User 입장에서 출력
        prompt = f"Target Workspace: `{self.target_project}` 에 대해 L1, L2 룰을 융합하고 로컬에 배포할 준비를 하세요."
        user_bubble = ChatBubble(role="User", initial_text=prompt)
        self.chat_container.mount(user_bubble)
        
        asyncio.create_task(self.run_pipeline(prompt))

    async def run_pipeline(self, prompt: str) -> None:
        from ..core.pipeline import PartiOpsPipeline
        try:
            self.status_bar.update("⏳ Pipeline is running... Please wait.")
            pipeline = PartiOpsPipeline(target_project_id=self.target_project)
            
            async for event in pipeline.run(command_prompt=prompt):
                text_output = ""
                if getattr(event, "content", None) and getattr(event.content, "parts", None):
                    text_output = "".join([part.text for part in event.content.parts if part.text])
                
                agent_name = getattr(event, "author", "Pipeline")
                # author 이름이 user이면 TUI에선 이미 프롬프트를 띄웠거나 System 처리하므로 패스하거나 분기
                role_title = f"Agent ({agent_name})" if agent_name and agent_name.lower() != "user" else "Agent Pipeline"

                if text_output:
                    # 새로운 AI 응답 텍스트가 들어오거나 에이전트가 교체되었을 때
                    if not self.current_ai_bubble or self.current_ai_bubble.role != role_title:
                        self.current_ai_bubble = ChatBubble(role=role_title, initial_text="")
                        self.chat_container.mount(self.current_ai_bubble)
                    self.current_ai_bubble.append_text(text_output)
                    self.chat_container.scroll_end(animate=False)
                else:
                    # Content가 없는 상태 전환, System Event 등
                    event_name = getattr(event, "__class__", type(event)).__name__
                    if event_name not in ("ModelCallEvent", "ToolCallEvent"): # 노이즈 방지
                         sys_event = ChatBubble(role="System", initial_text=f"`{event_name}` 상태 진입 (Author: {agent_name})")
                         self.chat_container.mount(sys_event)
                         self.chat_container.scroll_end(animate=False)
                         self.current_ai_bubble = None # 다음 텍스트는 새로운 버블로
                     
            self.status_bar.update("✅ Done! You can exit by pressing 'q'.")
        except Exception as e:
            err_bubble = ChatBubble(role="System", initial_text=f"**Error Occurred:**\n```\n{str(e)}\n```")
            self.chat_container.mount(err_bubble)
            self.chat_container.scroll_end(animate=False)
            self.status_bar.update("❌ Pipeline Failed.")

def main():
    # .env 환경 변수 로드 (명령어 진입점이므로 가장 먼저 실행)
    load_dotenv()
    
    # 로그 디렉토리 보장 및 파일 로깅 설정 (TUI 화면 깨짐 방지 위해 파일로만 기록)
    os.makedirs("logs", exist_ok=True)
    logging.basicConfig(
        filename="logs/arti-ops-tui.log",
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Textual 내부 에러 로그 등도 파일에 남기도록 설정 가능
    # os.environ["TEXTUAL_LOG"] = "logs/textual.log"

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
