import os
import pytest
from dotenv import load_dotenv
load_dotenv()

from arti_ops.core.pipeline import PartiOpsPipeline

@pytest.mark.asyncio
@pytest.mark.skipif("GEMINI_API_KEY" not in os.environ, reason="Env vars are not set")
async def test_live_pipeline_execution():
    """
    실제 Gemini API와 연결된 PartiOpsPipeline의 초기 구동(Runner)이 정상적인지 확인합니다.
    """
    target_project_id = "TEST-LIVE-123"
    pipeline = PartiOpsPipeline(target_project_id)
    
    # 파이프라인 실행: 무거운 작업이나 툴 호출을 막기 위해 가벼운 인사만 보냄
    prompt = "안녕! 이건 라이브 통합 테스트야. 추가 작업이나 파일 탐색 없이 그냥 정상 종료(답변)해줘."
    
    events = []
    # 파이프라인 Generator 루프 확인
    async for event in pipeline.run(command_prompt=prompt, session_id="test-session-pipeline-live"):
        events.append(event)
        
    assert len(events) > 0
    
    # 마지막 응답 검증 (에이전트로부터 어떤 형태로든 답변을 받아야 함)
    final_output = ""
    for event in events:
        if getattr(event, "content", None) and event.content.parts:
            text = "".join([part.text for part in event.content.parts if part.text])
            if text:
                final_output += text
                
    assert final_output != ""
    print(f"\\n[Pipeline Response]: {final_output}")
