import os
import asyncio
import logging
from pydantic import ConfigDict

logger = logging.getLogger(__name__)

class GwsChatTool:
    """배포가 모두 완료된 후 가장 마지막에 요약 알림을 전송하는 단방향 통신 툴"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    @property
    def gws_space_id(self) -> str:
        return os.getenv("GWS_SPACE_ID", "")

    async def send_summary(self, project_id: str, summary: str) -> str:
        """최종 배포 후 요약 보고서를 GWS에 전송합니다."""
        if not self.gws_space_id:
            logger.warning("GWS_SPACE_ID is not set. Skipped summary webhook.")
            return "Skipped (No GWS_SPACE_ID)"

        message_body = f"✅ *arti-ops 배포 완료 요약* [{project_id}]\n\n---\n{summary}\n---"
        
        try:
            env = os.environ.copy()
            process = await asyncio.create_subprocess_exec(
                "gws", "chat", "+send", "--space", self.gws_space_id, "--text", message_body,
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, env=env
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                return f"Summary sent successfully to GWS space: {self.gws_space_id}"
            else:
                return f"Failed to send summary: {stderr.decode('utf-8')}"
        except Exception as e:
            return f"Error occurred: {str(e)}"
