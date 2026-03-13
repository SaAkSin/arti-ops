import os
import asyncio
from typing import AsyncGenerator
from google.adk.runner import Runner
from google.adk.database import Database
from google.adk.engine import WorkflowEngine, StreamEvent

from ..agents.profiler import get_profiler_agent
from ..agents.architect import get_architect_agent
from ..agents.verifier import get_verifier_agent
from ..agents.executor import get_executor_agent

from ..tools.bookstack import BookStackToolset
from ..tools.gws_chat import GwsChatTool
from ..tools.sandbox import SandboxTool

class PartiOpsPipeline:
    def __init__(self, target_project_id: str):
        self.target_project_id = target_project_id
        
        # 1. 툴 선언
        self.bookstack_tool = BookStackToolset()
        self.gws_chat_tool = GwsChatTool()
        self.sandbox_tool_factory = SandboxTool()
        self.sandbox_executor = self.sandbox_tool_factory.get_executor()
        
        # 2. 에이전트 선언
        self.profiler = get_profiler_agent()
        self.architect = get_architect_agent()
        self.verifier = get_verifier_agent()
        self.executor = get_executor_agent()
        
        # Runner 및 State DB 연결 설정 (로컬 SQLite 활용 예시)
        # 실제 환경에서는 sqlalchemy나 adk의 database module 주입
        self.db = Database(url=os.getenv("DATABASE_URL", "sqlite:///arti_ops_session.db"))
        
        self.runner = Runner(
            agents=[self.profiler, self.architect, self.verifier, self.executor],
            tools=[self.bookstack_tool, self.gws_chat_tool, self.sandbox_executor],
            database=self.db
        )

    async def run(self, command_prompt: str, session_id: str = None) -> AsyncGenerator[StreamEvent, None]:
        """
        초기 프롬프트를 전송하여 파이프라인을 실행시킵니다.
        Generator 형태로 로깅과 상태 스트림을 반환하여 TUI 화면에 실시간 노출시킵니다.
        """
        engine = WorkflowEngine(self.runner)
        
        # Self-correction loop 및 agent transition 은
        # Runner 내부의 router 또는 프롬프트 인스트럭션에 맞게 조정되거나
        # Orchestrator 에이전트를 두어 위임하게 됩니다.
        
        # 여기서는 단일 프롬프트 스트림 실행을 가정합니다.
        # 실제 구현에서는 루프 에이전트 기반 오케스트레이션을 정의합니다.
        async for event in engine.stream(prompt=command_prompt, session_id=session_id):
            yield event

    async def resume(self, session_id: str, action_response: dict) -> AsyncGenerator[StreamEvent, None]:
        """
        HITL 등 이유로 중단되었던(Pause) 세션을 콜백 값과 함께 다시 재개합니다.
        """
        engine = WorkflowEngine(self.runner)
        async for event in engine.resume(session_id=session_id, action_response=action_response):
            yield event
