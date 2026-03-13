import os
import pytest
from dotenv import load_dotenv
load_dotenv()

from google.genai.types import Content, Part
from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from arti_ops.agents.verifier import get_verifier_agent

@pytest.mark.asyncio
@pytest.mark.skipif("GEMINI_API_KEY" not in os.environ, reason="Env vars are not set")
async def test_live_verifier_agent_execution():
    """
    실제 Gemini API를 엮어 Verifier 에이전트가
    가상의 위반 스크립트를 보고, 문제점을 정확히 지적해 내는지 확인합니다.
    """
    # 1. 에이전트 준비
    verifier_agent = get_verifier_agent()

    # 2. ADK Runner 구성
    runner = Runner(
        app_name="arti-ops-verifier",
        agent=verifier_agent,
        session_service=InMemorySessionService(),
        auto_create_session=True
    )

    # 3. 테스트용 프롬프트 및 컨텍스트 (의도적으로 Rule 위반 상황 연출)
    prompt = """
다음은 이전 단계(Architect)에서 작성된 배포용 파이썬 스크립트입니다.

[L1 Global Rules]
- 모든 변수명은 snake_case를 사용.
- 외부 API 호출은 엄격히 금지.

[작성된 코드 내용]
```python
def fetchExternalData():
    import urllib.request
    resultData = urllib.request.urlopen("http://example.com").read()
    return resultData
```

코드 리뷰 부탁합니다. 위 규칙들에 어긋나는 부분이 있다면 구체적으로 지적해 주세요.
"""

    print(f"\n[Verifier Request]: {prompt}")

    # 4. Agent 구동 및 스트림 수집
    final_response = ""
    message_content = Content(role="user", parts=[Part.from_text(text=prompt)])

    async for event in runner.run_async(user_id="test_user", session_id="test_session", new_message=message_content):
        # Event 타입 중 Content를 포함한 객체에서 메시지 조각을 빼옵니다.
        if getattr(event, "content", None) and event.content.parts:
            text = "".join([part.text for part in event.content.parts if part.text])
            if text:
                final_response += text
                
    print("\n======= [Verifier Agent Response] =======")
    print(final_response)
    print("=========================================\n")

    # 문서 검증
    assert final_response != ""
    lower_response = final_response.lower()
    
    # 뱀표기법(snake_case) 위반 지적 여부 검증
    assert "snake_case" in lower_response or "camelcase" in lower_response
    # 외부 API 호출 위반 지적 여부 검증
    assert "외부 api" in lower_response or "api 호출" in lower_response or "urllib" in lower_response
