import os
import httpx
from typing import Optional, Dict, Any
from google.adk.tools import RestApiTool
from pydantic import BaseModel, ConfigDict, Field

class BookStackToolset(RestApiTool):
    """
    BookStack API 통합을 위한 ADK Toolset.
    Global(L1) 및 Workspace(L2) 정책을 마크다운 형태로 가져오고, 
    배포 결과를 Release Notes로 퍼블리시합니다.
    """
    api_url: str = Field(description="BookStack API Base URL", default_factory=lambda: os.getenv("BOOKSTACK_API_URL", ""))
    token_id: str = Field(description="BookStack API Token ID", default_factory=lambda: os.getenv("BOOKSTACK_TOKEN_ID", ""))
    token_secret: str = Field(description="BookStack API Token Secret", default_factory=lambda: os.getenv("BOOKSTACK_TOKEN_SECRET", ""))
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    def get_headers(self) -> Dict[str, str]:
        """BookStack API 인증 헤더를 반환합니다."""
        return {
            "Authorization": f"Token {self.token_id}:{self.token_secret}",
            "Content-Type": "application/json"
        }

    async def fetch_policies(self, scope_tag: str, project_id: Optional[str] = None) -> str:
        """
        BookStack에서 특정 Scope(L1/L2)의 마크다운 정책 문서를 조회합니다.
        
        Args:
            scope_tag (str): 'global' (L1) 또는 'workspace' (L2) 
            project_id (Optional[str]): workspace scope인 경우 조회할 프로젝트의 고유 식별자
            
        Returns:
            str: 마크다운 텍스트 형태의 정책 문서
        """
        if scope_tag == "workspace" and not project_id:
            return "Error: Workspace scope requires a project_id."
            
        # 실제 구현 시에는 북스택 페이지 검색 API를 호출하여 markdown 컨텐츠를 가져와야 합니다.
        # 아래는 가상의 테스트용 Mocking 응답입니다.
        if scope_tag == "global":
            return "# Global Rules (L1)\n1. Never use root access.\n2. All secrets must be encrypted."
        elif scope_tag == "workspace" and project_id:
            return f"# Workspace {project_id} Rules (L2)\n1. Use PostgreSQL\n2. Maintain 80% test coverage."
        
        return "No policies found."

    async def publish_sync_report(self, project_id: str, diff_md: str) -> str:
        """
        배포된 최신 룰과 Diff를 BookStack의 Release Note 페이지에 업데이트합니다.
        
        Args:
            project_id (str): 대상 프로젝트 식별자
            diff_md (str): 마크다운 형식의 Sync 리포트/Diff 내용
            
        Returns:
            str: 업데이트 결과 메세지
        """
        # 실제 구현에서는 BookStack API의 페이지 수정 (PUT) 호출을 진행합니다.
        # Mocking
        return f"Successfully updated Release Notes for project {project_id} with diff."

