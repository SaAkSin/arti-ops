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
            executor = ContainerCodeExecutor(image=self.image)
            
            # ADK v1.27.0+ ContainerCodeExecutor 의 코드 실행 메커니즘
            logger.info("SandboxTool: Executing python code snippet in container...")
            result = executor.run_code_snippet(code=code_snippet, auto_install_dependencies=True)
            
            output_lines = []
            if getattr(result, 'output', None):
                output_lines.append(f"STDOUT:\n{result.output}")
            if getattr(result, 'error', None):
                output_lines.append(f"STDERR:\n{result.error}")
                
            return "\n\n".join(output_lines) if output_lines else "Success: No output produced."
        except Exception as e:
            logger.exception("Sandbox execution failed")
            return f"Error executing code in sandbox: {e}"
