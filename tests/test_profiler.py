import pytest
import os
from arti_ops.agents.profiler import get_profiler_agent
from google.adk import Agent

def test_profiler_agent_initialization():
    """Profiler Agent 객체가 올바른 초기값과 지시어(Instructions)를 갖고 생성되는지 검증합니다."""
    # 사용자 정의 환경변수 주입 테스트
    os.environ["GEMINI_MODEL_FLASH"] = "test-gemini-model"
    
    agent = get_profiler_agent()
    
    # 타입 검증
    assert isinstance(agent, Agent)
    
    # 식별자 및 이름 검증
    assert getattr(agent, "name", "") == "context_profiler"
    
    # 모델명 매핑 검증
    assert getattr(agent, "model", "") == "test-gemini-model"
    
    # 핵심 시스템 프롬프트(Instructions) 내용 검증
    inst = getattr(agent, "instruction", "")
    assert "컨텍스트 스캐너 'Profiler'" in inst
    assert "BookStackToolset을 호출하여" in inst
    assert "Global Rule (L1)과 Project Workspace Rule (L2)을 수집" in inst
