import os
import logging
from typing import List
from google.adk.tools import BaseTool, FunctionTool
from google.adk.tools.base_toolset import BaseToolset

logger = logging.getLogger(__name__)

class FileIOToolset(BaseToolset):
    """로컬 호스트 디렉토리를 탐색하고 AI가 생성한 배포 스크립트를 파일로 안전하게 저장하는 도구"""
    
    async def get_tools(self, context=None) -> List[BaseTool]:
        return [
            FunctionTool(func=self.write_file),
            FunctionTool(func=self.read_file)
        ]

    async def write_file(self, relative_path: str, content: str) -> str:
        """
        주어진 문자열을 파일로 저장합니다.
        보안(Path Traversal 방지)을 위해 현재 워크스페이스의 '.agents/' 폴더 내부로 쓰기가 강제 격리됩니다.
        """
        try:
            base_dir = os.path.abspath(os.getcwd())
            target_path = os.path.abspath(os.path.join(base_dir, ".agents", relative_path))
            
            # 디렉토리 이탈 공격 방어
            if not target_path.startswith(os.path.join(base_dir, ".agents")):
                return "Error: Security Violation. '.agents' 폴더 내부에만 저장할 수 있습니다."
                
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info(f"File successfully written to {target_path}")
            return f"Success: 파일이 {target_path} 에 저장되었습니다."
        except Exception as e:
            return f"Error writing file: {str(e)}"

    async def read_file(self, relative_path: str) -> str:
        """주어진 상대 경로의 파일 내용을 읽어옵니다."""
        try:
            target_path = os.path.abspath(relative_path)
            if not os.path.exists(target_path):
                return "Error: File not found."
            with open(target_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            return f"Error reading file: {str(e)}"
