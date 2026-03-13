import os
from typing import Dict, Any
from google.adk.tools import LongRunningFunctionTool
from pydantic import ConfigDict, Field
import httpx

class GwsChatTool(LongRunningFunctionTool):
    """
    GWS Chat Webhook을 통해 배포 전 파일 변경 사항이나 충돌 사항을 알리고,
    PM/Manager의 승인(Resume)이 있을 때까지 ADK 파이프라인 엔진을 대기(Pause)시키는 HITL 툴.
    """
    webhook_url: str = Field(
        description="GWS Chat Webhook URL",
        default_factory=lambda: os.getenv("GWS_WEBHOOK_URL", "")
    )
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    async def request_approval(self, project_id: str, diff_md: str, conflict_reason: str) -> None:
        """
        GWS 채팅방으로 승인 요청 메시지를 전송합니다 (Async webhook call).
        
        Args:
            project_id (str): 대상 프로젝트 아이디
            diff_md (str): 적용될 파일 내용 (Diff)
            conflict_reason (str): 충돌 사유나 특이사항
        """
        # 실제 환경에서는 httpx.AsyncClient 등을 사용하여 webhook_url에 POST 요청
        print(f"[{project_id}] 배포 승인 요청 GWS 메시지 발송됨.")
        print(f"사유: {conflict_reason}")
        print(f"Diff 요약: \n{diff_md}")
        # 실제 구현에서는 webhook_url 검증 및 HTTP POST 로직 추가
    
    # Run은 LongRunningFunctionTool의 표준 호출 메서드를 재정의 또는 확장에 사용
    async def run(self, project_id: str, diff_md: str, conflict_reason: str) -> Dict[str, Any]:
        """
        이 메서드가 호출되면 LongRunningFunctionTool의 특성에 의해 파이프라인이 즉시 일시정지(Yield)됩니다.
        호출 전에 승인 요청 메시지를 Webhook으로 보냅니다.
        """
        await self.request_approval(project_id, diff_md, conflict_reason)
        # return 한 내용은 Runner 쪽에서 일시 정지(Pause) 이벤트를 식별하는 데이터로 활용됩니다.
        return {
            "status": "pending_approval",
            "project_id": project_id,
            "message": "Waiting for GWS approval callback"
        }
