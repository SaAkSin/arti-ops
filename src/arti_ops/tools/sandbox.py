import os
import logging
from typing import Any
from pydantic import BaseModel, Field
from google.adk.tools import BaseTool, FunctionTool
from google.adk.tools.base_toolset import BaseToolset

logger = logging.getLogger(__name__)

class SandboxTool(BaseToolset):
    """
    격리된 환경(Docker/Podman Sandbox) 내에서 AI 에이전트가 만든 
    배포 관련 파이썬이나 쉘 스크립트를 Dry-Run 할 수 있는 툴셋 클래스입니다.
    """
    image: str = "python:3.10-slim"
    timeout_seconds: int = 30
    
    async def get_tools(self, context=None) -> list[BaseTool]:
        return [
            FunctionTool(func=self.run_python_script)
        ]
        
    async def run_python_script(self, code_snippet: str) -> str:
        """
        주어진 파이썬 코드 문자열을 안전한 샌드박스(컨테이너) 환경에서 실행하고 그 결과를 반환합니다.
        
        Args:
            code_snippet (str): 실행할 파이썬 소스 코드 (문자열)
            
        Returns:
            str: stdout 및 stderr 등 실행 결과 로그
        """
        try:
            from google.adk.code_executors import ContainerCodeExecutor
            from google.adk.code_executors.code_execution_utils import CodeExecutionInput
            from google.adk.agents.invocation_context import InvocationContext
            from google.adk.sessions import Session
            from google.adk.agents.base_agent import BaseAgent
            
            executor = ContainerCodeExecutor(image=self.image)
            
            # ADK v1.27.0+ ContainerCodeExecutor 의 코드 실행 메커니즘
            logger.info("SandboxTool: Executing python code snippet in container...")
            
            # 더미 InvocationContext 생성 (execute_code 에 필수)
            mock_session = Session(id="sandbox_test", appName="arti-ops", userId="test_user")
            # 최소한의 속성을 가진 더미 에이전트 클래스 정의
            class MockAgent(BaseAgent):
                def __init__(self):
                    super().__init__(name="mock", description="")
                async def _invoke(self, *args, **kwargs):
                    pass
            mock_agent = MockAgent()
            from google.adk.sessions.in_memory_session_service import InMemorySessionService
            mock_session_service = InMemorySessionService()
            
            mock_context = InvocationContext(
                invocation_id="test_inv",
                session=mock_session,
                session_service=mock_session_service,
                agent=mock_agent,
                agent_states={},
                end_of_agents={},
                end_invocation=False,
                token_compaction_checked=False
            )
            
            input_data = CodeExecutionInput(code=code_snippet, input_files=[])
            # v1.27.0+ 에서는 execute_code 비동기/동기 여부 확인 필요, 일반적으론 async
            # 만약 동기 함수라면 await 없이 실행해야 함
            import inspect
            if inspect.iscoroutinefunction(executor.execute_code):
                result = await executor.execute_code(invocation_context=mock_context, code_execution_input=input_data)
            else:
                result = executor.execute_code(invocation_context=mock_context, code_execution_input=input_data)
            
            output_lines = []
            if getattr(result, 'stdout', None):
                output_lines.append(f"STDOUT:\n{result.stdout}")
            if getattr(result, 'stderr', None):
                output_lines.append(f"STDERR:\n{result.stderr}")
                
            return "\n\n".join(output_lines) if output_lines else "Success: No output produced."
        except Exception as e:
            logger.exception("Sandbox execution failed")
            error_msg = str(e)
            if "Connection" in error_msg or "FileNotFoundError" in error_msg:
                return f"Error: 샌드박스 엔진(Docker/Podman)에 연결할 수 없습니다. Linux 환경의 경우 터미널에서 'systemctl --user enable --now podman.socket' 실행 및 'export DOCKER_HOST=unix://$XDG_RUNTIME_DIR/podman/podman.sock' 설정이 필요합니다. 상세 에러: {error_msg}"
            return f"Error executing code in sandbox: {error_msg}"
