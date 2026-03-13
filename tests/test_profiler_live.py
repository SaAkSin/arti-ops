import pytest
import os
from dotenv import load_dotenv

load_dotenv()

from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part
from arti_ops.agents.profiler import get_profiler_agent
from arti_ops.tools.bookstack import BookStackToolset

@pytest.mark.asyncio
@pytest.mark.skipif("BOOKSTACK_API_URL" not in os.environ or "GEMINI_API_KEY" not in os.environ, reason="Env vars are not set")
async def test_live_profiler_agent_execution():
    """
    실제 BookStackToolset 과 Gemini API를 엮어 Profiler 에이전트가 
    Context 스캐닝 후 요약 리포트를 잘 만들어내는지 확인합니다.
    """
    # 1. 툴 및 에이전트 준비
    bookstack_tool = BookStackToolset()
    profiler_agent = get_profiler_agent(tools=[bookstack_tool])
    
    # 2. ADK Runner 구성
    runner = Runner(
        app_name="arti-ops-profiler",
        agent=profiler_agent,
        session_service=InMemorySessionService(),
        auto_create_session=True
    )
    
    # 3. 테스트용 프롬프트 및 컨텍스트
    prompt = "현재 arti-ops 프로젝트의 Workspace 룰(L2)과 Global 룰(L1)을 수집하고 리포트를 만들어주세요."
    
    print(f"\n[Profiler Request]: {prompt}")
    
    # 4. Agent 구동 및 스트림 수집
    final_response = ""
    message_content = Content(role="user", parts=[Part.from_text(text=prompt)])
    
    async for event in runner.run_async(user_id="test_user", session_id="test_session", new_message=message_content):
        # Event 타입 중 Content를 포함한 객체에서 메시지 조각을 빼옵니다.
        if getattr(event, "content", None) and event.content.parts:
            text = "".join([part.text for part in event.content.parts if part.text])
            if text:
                final_response += text
    print("=========================================\n")
    
    # 문서 검증
    assert final_response != ""
    assert len(final_response) > 50
