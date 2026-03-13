from google.adk.tools import ContainerCodeExecutor
from pydantic import BaseModel, Field

class SandboxTool(BaseModel):
    """
    격리된 환경(Docker/Podman Sandbox) 내에서 AI 에이전트가 만든 
    배포 관련 파이썬이나 쉘 스크립트를 Dry-Run 할 수 있는 툴 팩토리 클래스입니다.
    ADK의 ContainerCodeExecutor를 인스턴스화 하여 반환합니다.
    """
    image: str = Field(default="python:3.10-slim", description="샌드박스에서 사용할 기반 이미지")
    timeout_seconds: int = Field(default=30, description="스크립트 실행 타임아웃")
    
    def get_executor(self) -> ContainerCodeExecutor:
        """
        배포 스크립트를 테스트할 컨테이너 실행기를 초기화하여 반환합니다.
        
        Returns:
            ContainerCodeExecutor
        """
        # 실제 구현에서는 docker SDK 또는 설정들을 바인딩할 수 있습니다.
        # ContainerCodeExecutor는 run_code_snippet 등의 메서드를 통해
        # 코드 구문을 안전하게 컨테이너 안에서 실행하고 stdout/stderr를 반환합니다.
        
        executor = ContainerCodeExecutor(
            image=self.image,
        )
        # Timeout 설정이나 Volume 바인딩 옵션들은 프로젝트 환경에 맞춰 추가로 주입
        
        return executor
