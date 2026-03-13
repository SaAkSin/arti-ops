import os
import asyncio
from typing import Dict, Any
from google.adk.tools import LongRunningFunctionTool
from pydantic import ConfigDict, Field

class GwsChatTool(LongRunningFunctionTool):
    """
    gws CLI를 통해 배포 전 파일 변경 사항이나 충돌 사항을 알리고,
    PM/Manager의 승인(Resume)이 있을 때까지 ADK 파이프라인 엔진을 대기(Pause)시키는 HITL 툴.
    """
    gws_space_id: str = Field(
        description="메시지를 보낼 GWS Chat 스페이스 아이디 (예: spaces/XXXXX)",
        default_factory=lambda: os.getenv("GWS_SPACE_ID", "")
    )
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    async def request_approval(self, project_id: str, diff_md: str, conflict_reason: str) -> None:
        """
        gws CLI 쉘 명령어로 메시지를 전송합니다.
        
        Args:
            project_id (str): 대상 프로젝트 아이디
            diff_md (str): 적용될 파일 내용 (Diff)
            conflict_reason (str): 충돌 사유나 특이사항
        """
        if not self.gws_space_id:
            print("Warning: GWS_SPACE_ID is not set. Skipped CLI webhook.")
            return

        message_body = (
            f"🚀 *arti-ops 배포 승인 요청* [{project_id}]\n\n"
            f"**충돌/보고 사유:** {conflict_reason}\n\n"
            f"---\n\n{diff_md}"
        )

        try:
            # gws cli 실행 시 사용자 OS의 기본 전역 자격 증명(~/.config/gws)을 인식하여 메시지를 발송합니다.
            process = await asyncio.create_subprocess_exec(
                "gws", "chat", "send",
                "--space", self.gws_space_id,
                "--message", message_body,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                print(f"[{project_id}] GWS 메시지 발송 완료 via CLI.")
            else:
                print(f"[{project_id}] GWS 메시지 발송 실패: {stderr.decode('utf-8')}")

        except Exception as e:
            print(f"gws cli 호출 중 에러 발생: {e}")
    
    # Run은 LongRunningFunctionTool의 표준 호출 메서드를 재정의 또는 확장에 사용
    async def run(self, project_id: str, diff_md: str, conflict_reason: str) -> Dict[str, Any]:
        """
        이 메서드가 호출되면 LongRunningFunctionTool의 특성에 의해 파이프라인이 즉시 일시정지(Yield)됩니다.
        호출 전에 gws CLI를 통해 승인 요청 메시지를 보냅니다.
        """
        await self.request_approval(project_id, diff_md, conflict_reason)
        # return 한 내용은 Runner 쪽에서 일시 정지(Pause) 이벤트를 식별하는 데이터로 활용됩니다.
        return {
            "status": "pending_approval",
            "project_id": project_id,
            "message": "Waiting for GWS approval callback"
        }
