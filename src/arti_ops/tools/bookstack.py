import os
import httpx
import logging
from typing import Optional, Dict, Any
from google.adk.tools import BaseTool, FunctionTool
from google.adk.tools.base_toolset import BaseToolset

logger = logging.getLogger(__name__)
from pydantic import ConfigDict, Field

class BookStackToolset(BaseToolset):
    """
    BookStack API 통합을 위한 ADK Toolset.
    Global(L1) 및 Workspace(L2) 정책을 마크다운 형태로 가져오고, 
    배포 결과를 Release Notes로 퍼블리시합니다.
    """
    def __init__(self, **kwargs):
        super().__init__()
        self.api_url = os.getenv("BOOKSTACK_API_URL", "")
        self.token_id = os.getenv("BOOKSTACK_TOKEN_ID", "")
        self.token_secret = os.getenv("BOOKSTACK_TOKEN_SECRET", "")

    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    async def get_tools(self, context=None) -> list[BaseTool]:
        """ADK 에이전트가 호출할 기능들의 FunctionTool 리스트를 반환합니다."""
        return [
            FunctionTool(func=self.fetch_policies),
            FunctionTool(func=self.publish_sync_report)
        ]
    
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
            
        book_slug = "antigravity-global-policy" if scope_tag == "global" else f"workspace-{project_id}"
            
        async with httpx.AsyncClient() as client:
            headers = self.get_headers()
            combined_markdown = []
            
            try:
                # 1. 대상 책(Book) ID 조회
                books_url = f"{self.api_url}/books"
                books_res = await client.get(books_url, headers=headers, params={"filter[slug]": book_slug})
                books_res.raise_for_status()
                books_data = books_res.json().get("data", [])
                
                if not books_data:
                    return f"Error: Book not found for slug '{book_slug}'"
                
                book_id = books_data[0]["id"]
                
                # 2. 책 상세 정보 조회 (하위 챕터 및 페이지 트리 구조 획득)
                book_detail_url = f"{self.api_url}/books/{book_id}"
                book_detail_res = await client.get(book_detail_url, headers=headers)
                book_detail_res.raise_for_status()
                
                contents = book_detail_res.json().get("contents", [])
                
                # 3. rules, skills 챕터 탐색
                for target in ["rules", "skills"]:
                    chapter = next((c for c in contents if c.get("type") == "chapter" and c.get("slug") == target), None)
                    
                    if not chapter:
                        logger.warning(f"====== [BookStack API] No '{target}' chapter found in '{book_slug}' ======")
                        combined_markdown.append(f"<!-- No {target} chapter found in {book_slug} -->")
                        continue
                        
                    combined_markdown.append(f"## {target.capitalize()} ({scope_tag.capitalize()})\n")
                    
                    # 4. 챕터에 소속된 페이지들의 마크다운 내용을 긁어옴
                    pages = chapter.get("pages", [])
                    if not pages:
                        combined_markdown.append(f"<!-- No pages in {target} chapter -->")
                        continue
                        
                    for page_info in pages:
                        page_id = page_info["id"]
                        page_url = f"{self.api_url}/pages/{page_id}"
                        page_res = await client.get(page_url, headers=headers)
                        page_res.raise_for_status()
                        
                        md_content = page_res.json().get("markdown", "")
                        combined_markdown.append(f"### {page_info.get('name')}\n\n{md_content}")
                        
                        logger.info(f"====== [BookStack API] Fetched Page '{page_info.get('name')}' in Chapter '{target}' ======\n{md_content}\n=======================================================")
                
                return "\n\n".join(combined_markdown)
                
            except Exception as e:
                logger.error(f"====== [BookStack API] Error connecting for '{book_slug}': {str(e)} ======")
                return f"Error connecting to BookStack API: {str(e)}"

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
                
                # 페이지 내용 가져오기 (GET)
                page_url = f"{self.api_url}/pages/{page_id}"
                get_res = await client.get(page_url, headers=headers)
                get_res.raise_for_status()
                existing_markdown = get_res.json().get("markdown", "")
                
                # 내용 이어붙이기 (Append)
                updated_markdown = f"{existing_markdown}\n\n---\n\n## New Deployment\n\n{diff_md}"
                
                # 페이지 내용 덮어쓰기 (PUT)
                payload = {
                    "markdown": updated_markdown
                }
                
                put_res = await client.put(page_url, headers=headers, json=payload)
                put_res.raise_for_status()
                
                return f"Successfully updated Release Notes for project {project_id}"
                
            except Exception as e:
                return f"Error publishing sync report: {str(e)}"

