import os
import asyncio
from typing import AsyncGenerator
from google.adk import Runner
from google.adk import Agent
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part
from typing import AsyncGenerator

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
        
        try:
            self.sandbox_executor = self.sandbox_tool_factory.get_executor()
        except ImportError:
            self.sandbox_executor = None
            # TUI 환경에서 로깅 모듈을 통해 안내 가능하도록 향후 추가
        
        # 2. 에이전트 선언
        self.profiler = get_profiler_agent()
        self.architect = get_architect_agent()
        self.verifier = get_verifier_agent()
        self.executor = get_executor_agent()
        
        # Runner (로컬 상태 연동 등을 지원하는 실제 adk 구현에 맞게 조정)
        self.runner = Runner(
            app_name="arti-ops-pipeline",
            # 향후 Multi-agent 시스템으로 Orchestrator를 넣을 수 있지만 
            # 초기 버전에서는 메인 agent 하나 또는 순차 호출 방식을 정의해야 합니다.
            # ADK v2.0 스펙에 맞춰 여기서는 일단 profiler를 진입점으로 둡니다.
            agent=self.profiler,
            session_service=InMemorySessionService(),
            auto_create_session=True
        )

    async def run(self, command_prompt: str, session_id: str = None) -> AsyncGenerator[any, None]:
        """
        초기 프롬프트를 전송하여 파이프라인(Profiler)을 실행시킵니다.
        """
        message_content = Content(role="user", parts=[Part.from_text(text=command_prompt)])
        async for event in self.runner.run_async(user_id="cli_user", session_id=session_id or "default_session", new_message=message_content):
            yield event

    async def resume(self, session_id: str, action_response: dict) -> AsyncGenerator[any, None]:
        """
        HITL 등 이유로 중단되었던(Pause) 세션을 다시 재개합니다. (향후 callback 연동)
        """
        # 현재 ADK Runner에서 지원하는 resume 로직에 맞게 연동 (임시 구현)
        yield {"status": "resumed"}
