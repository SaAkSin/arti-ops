import os
import pytest
from dotenv import load_dotenv
load_dotenv()

from google.genai.types import Content, Part
from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from arti_ops.agents.executor import get_executor_agent

@pytest.mark.asyncio
@pytest.mark.skipif("GEMINI_API_KEY" not in os.environ, reason="Env vars are not set")
async def test_live_executor_agent_execution():
    """
    실제 Gemini API를 엮어 Executor 에이전트가
    전달받은 가상의 스크립트 실행 플랜을 검토하고 수행 결과를 내는지 확인합니다.
    (현재 툴이 주입되지 않은 순수 에이전트 추론 동작 검증)
    """
    # 1. 에이전트 준비
    executor_agent = get_executor_agent()

    # 2. ADK Runner 구성
    runner = Runner(
        app_name="arti-ops-executor",
        agent=executor_agent,
        session_service=InMemorySessionService(),
        auto_create_session=True
    )

    # 3. 테스트용 프롬프트
    prompt = """
다음은 검증을 통과한 파이썬 스크립트 내용입니다.

```python
import os
def main():
    print("Deploying artifacts...")
    os.makedirs("logs", exist_ok=True)
    with open("logs/deploy_log.txt", "w") as f:
        f.write("Deploy successful.")
main()
```

위 스크립트를 받은 배포 집행관으로서, 로컬 파일 쓰기(File I/O) 적용 및 BookStack 동기화 퍼블리시 작업을 수행해야 합니다.
당신의 다음 행동 계획을 요약 서술해 주세요.
"""

    print(f"\n[Executor Request]: {prompt}")

    # 4. Agent 구동 및 스트림 수집
    final_response = ""
    message_content = Content(role="user", parts=[Part.from_text(text=prompt)])

    async for event in runner.run_async(user_id="test_user", session_id="test_session", new_message=message_content):
        # Event 타입 중 Content를 포함한 객체에서 메시지 조각을 빼옵니다.
        if getattr(event, "content", None) and event.content.parts:
            text = "".join([part.text for part in event.content.parts if part.text])
            if text:
                final_response += text
                
    print("\n======= [Executor Agent Response] =======")
    print(final_response)
    print("=========================================\n")

    # 문서 검증
    assert final_response != ""
    lower_response = final_response.lower()
    
    # 지시문(instruction)에 포함된 핵심 키워드가 언급되는지 확인
    assert "sandbox" in lower_response or "샌드박스" in lower_response or "가상" in lower_response or "dry-run" in lower_response or "파일 쓰기" in lower_response or "bookstack" in lower_response or "북스택" in lower_response
    assert "deploy_log.txt" in lower_response or "deploying artifacts" in lower_response or "로컬" in lower_response
