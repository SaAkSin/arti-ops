import os
import pytest
from unittest.mock import patch
from arti_ops.agents.profiler import get_profiler_agent
from google.adk import Agent


def test_profiler_agent_initialization():
    """Profiler Agent 객체가 올바른 초기값과 지시어(Instructions)를 갖고 생성되는지 검증합니다."""
    agent = get_profiler_agent()

    # 타입 검증
    assert isinstance(agent, Agent)

    # 식별자 및 이름 검증
    assert getattr(agent, "name", "") == "context_profiler"

    # 핵심 시스템 프롬프트(Instructions) 내용 검증 (현재 profiler.py 기준)
    inst = getattr(agent, "instruction", "")
    assert "Context Profiler" in inst
    assert ".agents/" in inst
