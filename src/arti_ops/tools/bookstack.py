import os
import httpx
import logging
import asyncio
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
    _ui_queue: Any = None # 클래스 변수로 선언하여 복제 시에도 참조 유지

    @classmethod
    def set_ui_queue(cls, queue: asyncio.Queue):
        cls._ui_queue = queue

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
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
                        page_name = page_info.get("name", f"page_{page_id}")
                        page_url = f"{self.api_url}/pages/{page_id}"
                        page_res = await client.get(page_url, headers=headers)
                        page_res.raise_for_status()
                        
                        md_content = page_res.json().get("markdown", "")
                        
                        # 명시적인 로컬 매핑 경로 주입
                        if target == "rules":
                            expected_path = f".agents/{target}/{page_name}.md"
                        else:  # skills 등 기타
                            expected_path = f".agents/{target}/{page_name}/SKILL.md"
                        combined_markdown.append(f"### {page_name} (Expected Path: {expected_path})\n\n{md_content}")
                        
                        logger.info(f"====== [DEBUG UI_QUEUE] type is: {type(self._ui_queue)} ======")
                        if getattr(self, "_ui_queue", None):
                            await self._ui_queue.put({
                                "type": "ui_message",
                                "data": {
                                    "type": "subnode_add",
                                    "agent": "context_profiler",
                                    "message": f"☁️ 위키 연동: {expected_path}",
                                    "color": "cyan"
                                }
                            })
                            logger.info(f"====== [DEBUG UI_QUEUE] put message to ui_queue for {page_name}.md ======")
                        else:
                            logger.error(f"====== [DEBUG UI_QUEUE] ui_queue is NONE for {page_name}.md! ======")
                        
                        logger.info(f"====== [BookStack API] Fetched Page '{page_name}' in Chapter '{target}' ======\n{md_content}\n=======================================================")
                
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

    async def get_upsert_plan(self, project_id: str) -> list[dict]:
        """로컬 .agents 데이터를 스캔하고 BookStack과 비교하여 배포 계획을 생성합니다."""
        plan = []
        book_slug = f"workspace-{project_id}"
        
        async with httpx.AsyncClient() as client:
            headers = self.get_headers()
            try:
                # 1. 대상 책(Book) ID 조회
                books_url = f"{self.api_url}/books"
                books_res = await client.get(books_url, headers=headers, params={"filter[slug]": book_slug})
                books_res.raise_for_status()
                books_data = books_res.json().get("data", [])
                
                if not books_data:
                    logger.error(f"Book not found for slug '{book_slug}'")
                    return plan
                book_id = books_data[0]["id"]
                
                # 2. 책 상세 정보 조회 (하위 챕터 획득)
                book_detail_url = f"{self.api_url}/books/{book_id}"
                book_detail_res = await client.get(book_detail_url, headers=headers)
                book_detail_res.raise_for_status()
                contents = book_detail_res.json().get("contents", [])
                
                chapters = {
                    "rules": next((c for c in contents if c.get("type") == "chapter" and c.get("slug") == "rules"), None),
                    "skills": next((c for c in contents if c.get("type") == "chapter" and c.get("slug") == "skills"), None)
                }

                # 3. 로컬 파일 스캔 및 비교
                base_dir = os.path.join(os.getcwd(), ".agents")
                targets = [
                    ("rules", os.path.join(base_dir, "rules")),
                    ("skills", os.path.join(base_dir, "skills"))
                ]
                
                for target_type, target_dir in targets:
                    chapter = chapters.get(target_type)
                    if not chapter:
                        logger.warning(f"No {target_type} chapter found in {book_slug}.")
                        continue
                        
                    chapter_id = chapter["id"]
                    existing_pages = {p["name"]: p["id"] for p in chapter.get("pages", [])}
                    
                    if not os.path.exists(target_dir):
                        continue
                        
                    if target_type == "rules":
                        for filename in os.listdir(target_dir):
                            if filename.endswith(".md"):
                                page_name = filename[:-3]
                                local_path = os.path.join(target_dir, filename)
                                rel_path = f".agents/rules/{filename}"
                                with open(local_path, "r", encoding="utf-8") as f:
                                    content = f.read()
                                
                                page_id = existing_pages.get(page_name)
                                action = "Update" if page_id else "Create"
                                plan.append({
                                    "name": page_name,
                                    "type": target_type,
                                    "rel_path": rel_path,
                                    "content": content,
                                    "action": action,
                                    "chapter_id": chapter_id,
                                    "page_id": page_id
                                })
                    elif target_type == "skills":
                        for skill_name in os.listdir(target_dir):
                            skill_dir = os.path.join(target_dir, skill_name)
                            if os.path.isdir(skill_dir):
                                skill_file = os.path.join(skill_dir, "SKILL.md")
                                if os.path.exists(skill_file):
                                    rel_path = f".agents/skills/{skill_name}/SKILL.md"
                                    with open(skill_file, "r", encoding="utf-8") as f:
                                        content = f.read()
                                        
                                    page_name = skill_name
                                    page_id = existing_pages.get(page_name)
                                    action = "Update" if page_id else "Create"
                                    plan.append({
                                        "name": page_name,
                                        "type": target_type,
                                        "rel_path": rel_path,
                                        "content": content,
                                        "action": action,
                                        "chapter_id": chapter_id,
                                        "page_id": page_id
                                    })
            except Exception as e:
                logger.error(f"Error generating upsert plan: {e}")
                
        return plan

    async def execute_upsert(self, plan: list[dict]) -> None:
        """선택된 배포 계획을 실제로 BookStack에 작성합니다."""
        async with httpx.AsyncClient() as client:
            headers = self.get_headers()
            
            for item in plan:
                try:
                    payload = {
                        "name": item["name"],
                        "markdown": item["content"],
                        "chapter_id": item["chapter_id"]
                    }
                    if item["action"] == "Create":
                        url = f"{self.api_url}/pages"
                        res = await client.post(url, headers=headers, json=payload)
                        res.raise_for_status()
                        logger.info(f"Created page: {item['name']}")
                    elif item["action"] == "Update":
                        url = f"{self.api_url}/pages/{item['page_id']}"
                        res = await client.put(url, headers=headers, json=payload)
                        res.raise_for_status()
                        logger.info(f"Updated page: {item['name']}")
                except Exception as e:
                    logger.error(f"Failed to {item['action']} page {item['name']}: {e}")

