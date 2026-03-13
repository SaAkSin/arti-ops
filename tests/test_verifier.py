import os
from google.adk import Agent
from arti_ops.agents.verifier import get_verifier_agent

def test_verifier_agent_initialization():
    """
    Verifier 에이전트가 올바른 파라미터로 생성되는지 확인합니다.
    """
    # 에이전트 생성
    agent = get_verifier_agent()
    
    # 타입 검증
    assert isinstance(agent, Agent)
    
    # 속성 검증
    assert agent.name == "critical_verifier"
    assert "깐깐한 감사관 'Verifier' (Red-Team)" in agent.instruction
    assert "L1 Global Rule을 조금이라도 위반하는 내용이 있는지 심사" in agent.instruction
    assert agent.model == os.getenv("GEMINI_MODEL_PRO", "gemini-2.5-pro")
