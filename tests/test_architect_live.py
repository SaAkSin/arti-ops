import os
import pytest
from dotenv import load_dotenv
load_dotenv()

from google.genai.types import Content, Part
from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from arti_ops.agents.architect import get_architect_agent

@pytest.mark.asyncio
@pytest.mark.skipif("GEMINI_API_KEY" not in os.environ, reason="Env vars are not set")
async def test_live_architect_agent_execution():
    """
    실제 Gemini API를 엮어 Architect 에이전트가
    가상의 정책(L1, L2) 컨텍스트를 받아 배포용 파이썬 스크립트를 잘 만들어내는지 확인합니다.
    """
    # 1. 툴 및 에이전트 준비 (Architect는 툴 없이 단독 프롬프트 처리로 시작 가능)
    architect_agent = get_architect_agent()

    # 2. ADK Runner 구성
    runner = Runner(
        app_name="arti-ops-architect",
        agent=architect_agent,
        session_service=InMemorySessionService(),
        auto_create_session=True
    )

    # 3. 테스트용 프롬프트 및 컨텍스트 (Profiler가 전달했다고 가정)
    prompt = """
현재 우리는 Python 프로젝트를 관리하고 있습니다. 
아래 수집된 L1(Global), L2(Workspace) 룰을 참고하여 
파일 쓰기(setup_logger.py 생성) 역할을 하는 배포용 파이썬 스크립트를 하나 작성하세요.

[L1 Global Rules]
- 모든 변수명은 snake_case를 사용.
- 로그 출력에는 반드시 `logging` 표준 모듈을 사용해야 함. print문 금지.

[L2 Workspace Rules]
- 이 프로젝트에서는 DEBUG 레벨의 로그를 항상 `project_debug.log` 파일에 남겨야 함.
- 포맷은 `%(asctime)s - %(name)s - %(levelname)s - %(message)s` 유지.

위 룰을 만족하는 로거 세팅 파이썬 코드를 작성하는 스크립트를 제공해 주세요.
출력에는 파이썬 코드 블록(```python) 내용만 포함해야 합니다.
"""

    print(f"\n[Architect Request]: {prompt}")

    # 4. Agent 구동 및 스트림 수집
    final_response = ""
    message_content = Content(role="user", parts=[Part.from_text(text=prompt)])

    async for event in runner.run_async(user_id="test_user", session_id="test_session", new_message=message_content):
        # Event 타입 중 Content를 포함한 객체에서 메시지 조각을 빼옵니다.
        if getattr(event, "content", None) and event.content.parts:
            text = "".join([part.text for part in event.content.parts if part.text])
            if text:
                final_response += text
                
    print("\n======= [Architect Agent Response] =======")
    print(final_response)
    print("=========================================\n")

    # 문서 검증
    assert final_response != ""
    assert "```python" in final_response.lower() # 파이썬 코드 블록이 있어야 함
    assert "logging" in final_response.lower() # logging 모듈 사용 지시 준수 여부
    assert "project_debug.log" in final_response.lower() # L2 룰 준수 여부
