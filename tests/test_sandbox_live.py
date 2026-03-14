import pytest
import sys

# docker 모듈이 깔려있는지 확인해서 없으면 라이브 테스트 생략
pytest.importorskip("docker", reason="docker 모듈 및 google-adk[extensions]가 없으므로 Sandbox 라이브 테스트를 스킵합니다.")

from arti_ops.tools.sandbox import SandboxTool

def test_sandbox_live_execution():
    """
    실제로 로컬 Docker/Podman 데몬과 연결하여 파이썬 스크립트가 잘 실행되는지 테스트힙니다.
    """
    tool = SandboxTool()
    tool.image = "python:3.10-slim"
    
    code = "print('Hello from sandbox!')"
    
    # ADK ContainerCodeExecutor 의 run_code_snippet 등 메서드를 호출하여 반환값 검증 (실제 구현에 따라 다름)
    import asyncio
    
    async def run_test():
        response = await tool.run_python_script(code)
        assert "Hello from sandbox!" in response
        
    asyncio.run(run_test())
