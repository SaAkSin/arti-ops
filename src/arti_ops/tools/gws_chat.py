import os
import asyncio
from typing import Dict, Any
from pydantic import ConfigDict
import logging

logger = logging.getLogger(__name__)

class GwsChatTool:
    """
    gws CLI를 통해 배포가 모두 완료된 후 가장 마지막에 요약 알림을 전송하는 단방향 통신 툴입니다.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    def __init__(self, **data):
        super().__init__()
        
    @property
    def gws_space_id(self) -> str:
        return os.getenv("GWS_SPACE_ID", "")

    async def send_summary(self, project_id: str, summary: str) -> str:
        """
        파이프라인의 배포가 모두 완료된 후 가장 마지막에 호출되는 단순 알림용(Non-blocking) 메서드입니다.
        """
        if not self.gws_space_id:
            logger.warning("GWS_SPACE_ID is not set. Skipped summary webhook.")
            return "Skipped (No GWS_SPACE_ID)"

        message_body = (
            f"✅ *arti-ops 배포 완료 요약* [{project_id}]\n\n"
            f"---\n{summary}\n---"
        )
        
        try:
            env = os.environ.copy()
            process = await asyncio.create_subprocess_exec(
                "gws", "chat", "+send",
                "--space", self.gws_space_id,
                "--text", message_body,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                logger.info(f"[{project_id}] 배포 요약 GWS 전송 완료.")
                return f"Summary sent successfully to GWS space: {self.gws_space_id}"
            else:
                err_msg = stderr.decode('utf-8')
                logger.error(f"[{project_id}] 배포 요약 발송 실패: {err_msg}")
                return f"Failed to send summary: {err_msg}"
                
        except Exception as e:
            logger.exception(f"gws summary 발송 중 에러 발생: {e}")
            return f"Error occurred: {str(e)}"
