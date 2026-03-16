import os
from google.adk import Agent
from arti_ops.agents.executor import get_executor_agent

def test_executor_agent_initialization():
    """
    Executor 에이전트가 올바른 파라미터로 생성되는지 확인합니다.
    """
    # 에이전트 생성
    agent = get_executor_agent()
    
    # 타입 검증
    assert isinstance(agent, Agent)
    
    # 속성 검증
    assert agent.name == "deployment_executor"
    assert "배포 집행관 'Executor'" in agent.instruction
    assert "write_file" in agent.instruction
    assert "send_summary" in agent.instruction
    assert agent.model == os.getenv("GEMINI_MODEL_FLASH", "gemini-2.5-flash")
