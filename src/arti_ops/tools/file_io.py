import os
import asyncio
import logging
from typing import List, Any
from google.adk.tools import BaseTool, FunctionTool
from google.adk.tools.base_toolset import BaseToolset

logger = logging.getLogger(__name__)

class FileIOToolset(BaseToolset):
    _ui_queue: Any = None

    @classmethod
    def set_ui_queue(cls, queue: asyncio.Queue):
        cls._ui_queue = queue
    
    async def get_tools(self, context=None) -> List[BaseTool]:
        return [
            FunctionTool(func=self.write_file),
            FunctionTool(func=self.read_file),
            FunctionTool(func=self.list_directory) # 🚨 신규 로컬 스캔 도구
        ]

    async def list_directory(self, relative_path: str = ".") -> str:
        """명령어가 실행된 로컬 프로젝트 기준의 파일 및 폴더 구조를 텍스트로 반환합니다."""
        try:
            base_dir = os.path.abspath(os.getcwd())
            target_path = os.path.abspath(os.path.join(base_dir, relative_path))
            
            if not target_path.startswith(base_dir):
                return "Error: Security Violation."
            if not os.path.exists(target_path):
                return f"Directory '{relative_path}' does not exist."
                
            if getattr(self, "_ui_queue", None):
                await self._ui_queue.put({
                    "type": "ui_message",
                    "data": {
                        "type": "subnode_add",
                        "agent": "context_profiler",
                        "message": f"📂 로컬 트리 스캔: {relative_path}",
                        "color": "green"
                    }
                })
                
            tree = []
            for root, dirs, files in os.walk(target_path):
                # 불필요한 무거운 폴더 제외 (AI 부하 방지)
                dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', '.venv', 'venv', 'node_modules']]
                level = root.replace(base_dir, '').count(os.sep)
                indent = ' ' * 4 * level
                tree.append(f"{indent}📁 {os.path.basename(root)}/")
                subindent = ' ' * 4 * (level + 1)
                for f in files:
                    tree.append(f"{subindent}📄 {f}")
            return "\n".join(tree)
        except Exception as e:
            return f"Error listing directory: {str(e)}"

    async def write_file(self, relative_path: str, content: str) -> str:
        try:
            base_dir = os.path.abspath(os.getcwd())
            target_path = os.path.abspath(os.path.join(base_dir, relative_path))
            
            if not target_path.startswith(os.path.join(base_dir, ".agents")):
                return "Error: Security Violation. 파일은 '.agents/' 폴더 내부에만 저장할 수 있습니다."
                
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(content)
            return f"Success: 파일이 {target_path} 에 저장되었습니다."
        except Exception as e:
            return f"Error writing file: {str(e)}"

    async def read_file(self, relative_path: str) -> str:
        try:
            target_path = os.path.abspath(relative_path)
            
            if getattr(self, "_ui_queue", None):
                await self._ui_queue.put({
                    "type": "ui_message",
                    "data": {
                        "type": "subnode_add",
                        "agent": "context_profiler",
                        "message": f"🔎 로컬 내용 독해: {relative_path}",
                        "color": "green"
                    }
                })
            if not os.path.exists(target_path):
                return "Error: File not found."
            with open(target_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            return f"Error reading file: {str(e)}"
