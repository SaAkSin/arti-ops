import os
import httpx
import logging
from typing import Optional, Dict, Any
from google.adk.tools import BaseTool

logger = logging.getLogger(__name__)
from pydantic import ConfigDict, Field

class BookStackToolset(BaseTool):
    """
    BookStack API 통합을 위한 ADK Toolset.
    Global(L1) 및 Workspace(L2) 정책을 마크다운 형태로 가져오고, 
    배포 결과를 Release Notes로 퍼블리시합니다.
    """
    def __init__(self, **kwargs):
        kwargs.setdefault("name", "BookStackToolset")
        kwargs.setdefault("description", "Fetches global and workspace rules from BookStack and publishes release notes.")
        super().__init__(**kwargs)
        self.api_url = os.getenv("BOOKSTACK_API_URL", "")
        self.token_id = os.getenv("BOOKSTACK_TOKEN_ID", "")
        self.token_secret = os.getenv("BOOKSTACK_TOKEN_SECRET", "")

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
            
        book_name = ""
        if scope_tag == "global":
            book_name = "[Antigravity] Global Policy"
        elif scope_tag == "workspace":
            book_name = f"[Workspace] {project_id}"
            
        async with httpx.AsyncClient() as client:
            headers = self.get_headers()
            combined_markdown = []
            
            for target in ["rules", "skills"]:
                # 검색 API를 통해 특정 Book 내부의 rules/skills 페이지 검색
                search_url = f"{self.api_url}/search"
                params = {"query": f'"{target}" +book:"{book_name}" +type:page'}
                
                try:
                    res = await client.get(search_url, headers=headers, params=params)
                    res.raise_for_status()
                    res_json = res.json()
                    
                    logger.info(f"====== [BookStack Search API] '{target}' in '{book_name}' ======\n{res_json}\n==================================================================")
                    
                    data = res_json.get("data", [])
                    
                    if not data:
                        logger.warning(f"====== [BookStack API] No page found for '{target}' in '{book_name}' ======")
                        combined_markdown.append(f"<!-- No {target} found in {book_name} -->")
                        continue
                        
                    # 매칭되는 페이지의 id 추출
                    page_id = data[0].get("id")
                    
                    # 페이지 내용(markdown) 추출
                    page_url = f"{self.api_url}/pages/{page_id}"
                    page_res = await client.get(page_url, headers=headers)
                    page_res.raise_for_status()
                    
                    md_content = page_res.json().get("markdown", "")
                    logger.info(f"====== [BookStack API] Fetched '{target}' from '{book_name}' ======\n{md_content}\n=======================================================")
                    
                    combined_markdown.append(f"## {target.capitalize()} ({scope_tag.capitalize()})\n\n{md_content}")
                    
                except Exception as e:
                    combined_markdown.append(f"<!-- Error connecting to BookStack API for {target}: {str(e)} -->")
            
            return "\n\n".join(combined_markdown)

    async def publish_sync_report(self, project_id: str, diff_md: str) -> str:
        """
        배포된 최신 룰과 Diff를 BookStack의 Release Note 페이지에 업데이트합니다.
        
        Args:
            project_id (str): 대상 프로젝트 식별자
            diff_md (str): 마크다운 형식의 Sync 리포트/Diff 내용
            
        Returns:
            str: 업데이트 결과 메세지
        """
        async with httpx.AsyncClient() as client:
            headers = self.get_headers()
            search_query = f"[Workspace] {project_id} Release Notes"
            search_url = f"{self.api_url}/search"
            params = {"query": f'"{search_query}" +type:page'}
            
            try:
                res = await client.get(search_url, headers=headers, params=params)
                res.raise_for_status()
                data = res.json().get("data", [])
                
                if not data:
                    return f"No Release Notes page found for {project_id}. Please create a page named '{search_query}' first."
                    
                page_id = data[0].get("id")
                
                # 페이지 내용 덮어쓰기 (PUT)
                page_url = f"{self.api_url}/pages/{page_id}"
                payload = {
                    "markdown": diff_md
                }
                
                put_res = await client.put(page_url, headers=headers, json=payload)
                put_res.raise_for_status()
                
                return f"Successfully updated Release Notes for project {project_id}"
                
            except Exception as e:
                return f"Error publishing sync report: {str(e)}"

