import os
from google.adk import Agent
from arti_ops.agents.architect import get_architect_agent

def test_architect_agent_initialization():
    """
    Architect 에이전트가 올바른 파라미터로 생성되는지 확인합니다.
    """
    # 에이전트 생성
    agent = get_architect_agent()
    
    # 타입 검증
    assert isinstance(agent, Agent)
    
    # 속성 검증
    assert agent.name == "skill_architect"
    assert "정책 병합관 'Architect'" in agent.instruction
    assert ".agents/rules/" in agent.instruction
    assert ".agents/skills/" in agent.instruction
    assert agent.model == os.getenv("GEMINI_MODEL_PRO", "gemini-3.1-pro-preview")
