import pytest
from unittest.mock import patch

from arti_ops.tools.sandbox import SandboxTool

def test_sandbox_tool_initialization():
    """
    SandboxTool이 기본 이미지와 타임아웃 설정을 잘 가지고 생성되는지 확인합니다.
    """
    tool = SandboxTool()
    assert tool.image == "python:3.10-slim"
    assert tool.timeout_seconds == 30

def test_sandbox_tool_get_executor():
    """
    get_executor 메서드 호출 시 ContainerCodeExecutor 객체를 올바르게 초기화하는지 확인합니다.
    """
    # 호스트 환경에 docker 의존성이 없는 경우 해당 테스트 스킵
    pytest.importorskip("docker", reason="docker 모듈 부족으로 테스트 스킵")
    
    tool = SandboxTool(image="alpine:latest", timeout_seconds=60)
    
    with patch("google.adk.code_executors.ContainerCodeExecutor") as mock_executor:
        executor = tool.get_executor()
        mock_executor.assert_called_once_with(image="alpine:latest")
