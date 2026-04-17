import os
import httpx
import logging
import asyncio
from typing import Optional, Dict, Any
from google.adk.tools import BaseTool, FunctionTool
from google.adk.tools.base_toolset import BaseToolset
from arti_ops.config import get_config

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
        self.api_url = get_config("BOOKSTACK_API_URL", "")
        self.token_id = get_config("BOOKSTACK_TOKEN_ID", "")
        self.token_secret = get_config("BOOKSTACK_TOKEN_SECRET", "")

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
                
                # 3. rules, skills, workflows 챕터 탐색
                for target in ["rules", "skills", "workflows"]:
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
                        
                        # [NEW] Extract and save attached scripts from markdown Fenced Code Blocks
                        import re
                        pattern = r'````(\w+)\s+filepath="([^"]+)"\r?\n(.*?)\r?\n````'
                        matches = list(re.finditer(pattern, md_content, re.DOTALL))
                        
                        if matches:
                            base_skill_dir = os.path.join(os.getcwd(), f".agents/{target}/{page_name}")
                            for match in matches:
                                lang, filepath, script_content = match.groups()
                                full_path = os.path.normpath(os.path.join(base_skill_dir, filepath))
                                
                                # 보안 검사 (디렉토리 이탈 방지)
                                if os.path.commonpath([base_skill_dir, full_path]) == base_skill_dir:
                                    os.makedirs(os.path.dirname(full_path), exist_ok=True)
                                    with open(full_path, "w", encoding="utf-8") as sf:
                                        sf.write(script_content)
                                    logger.info(f"Extracting script: {full_path}")
                                
                                md_content = md_content.replace(match.group(0), "")
                                
                            # 정리
                            md_content = md_content.replace("### 🛠️ Scripts & Dependencies", "").strip()
                            # 찌꺼기 공백 제어
                            md_content = re.sub(r'---\n+$', '', md_content).strip()

                        # 명시적인 로컬 매핑 경로 주입
                        if target in ["rules", "workflows"]:
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
                logger.error("BookStack 인증 정보를 찾을 수 없습니다. .artiops.toml 및 글로벌 인증 파일을 확인하세요.")
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

    async def create_workspace_book(self, project_id: str) -> bool:
        """새로운 워크스페이스용 책(Book)과 필수 챕터(rules, skills)를 생성합니다."""
        book_name = f"[Workspace] {project_id}"
        
        async with httpx.AsyncClient() as client:
            headers = self.get_headers()
            try:
                # 1. 책 생성
                url = f"{self.api_url}/books"
                payload = {
                    "name": book_name,
                    "description": f"Auto-generated workspace book for {project_id}"
                }
                res = await client.post(url, headers=headers, json=payload)
                res.raise_for_status()
                book_id = res.json()["id"]
                
                # 2. 필수 챕터 생성
                chapters_url = f"{self.api_url}/chapters"
                for target in ["rules", "skills", "workflows"]:
                    chap_payload = {
                        "book_id": book_id,
                        "name": target,
                        "description": f"Agent {target} storage"
                    }
                    c_res = await client.post(chapters_url, headers=headers, json=chap_payload)
                    c_res.raise_for_status()
                    
                # 3. 릴리즈 노트 페이지 스캐폴딩 (루트에 생성)
                page_url = f"{self.api_url}/pages"
                page_payload = {
                    "book_id": book_id,
                    "name": f"[Workspace] {project_id} Release Notes",
                    "markdown": f"# Release Notes\n\nAutomated deployments for {project_id} will be recorded here."
                }
                p_res = await client.post(page_url, headers=headers, json=page_payload)
                p_res.raise_for_status()
                
                logger.info(f"Successfully created workspace book and structure for {project_id}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to create workspace book: {e}")
                raise ValueError(f"워크스페이스 생성 실패: {e}")

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
                    error_msg = f"BookStack에서 '{book_slug}' 이름의 책(Book)을 찾을 수 없습니다. 위키에 접속하여 해당 프로젝트명으로 책을 먼저 생성해주세요."
                    logger.error(error_msg)
                    raise ValueError(error_msg)
                book_id = books_data[0]["id"]
                
                # 2. 책 상세 정보 조회 (하위 챕터 획득)
                book_detail_url = f"{self.api_url}/books/{book_id}"
                book_detail_res = await client.get(book_detail_url, headers=headers)
                book_detail_res.raise_for_status()
                contents = book_detail_res.json().get("contents", [])
                
                chapters = {
                    "rules": next((c for c in contents if c.get("type") == "chapter" and c.get("slug") == "rules"), None),
                    "skills": next((c for c in contents if c.get("type") == "chapter" and c.get("slug") == "skills"), None),
                    "workflows": next((c for c in contents if c.get("type") == "chapter" and c.get("slug") == "workflows"), None)
                }

                # 3. 로컬 파일 스캔 및 비교
                base_dir = os.path.join(os.getcwd(), ".agents")
                targets = [
                    ("rules", os.path.join(base_dir, "rules")),
                    ("skills", os.path.join(base_dir, "skills")),
                    ("workflows", os.path.join(base_dir, "workflows"))
                ]
                
                for target_type, target_dir in targets:
                    chapter = chapters.get(target_type)
                    if not chapter:
                        logger.warning(f"No {target_type} chapter found in {book_slug}.")
                        continue
                        
                    chapter_id = chapter["id"]
                    
                    # 챕터 상세 API를 호출하여 정확한 하위 페이징 정보를 가져온다 (버그 픽스)
                    chapter_detail_url = f"{self.api_url}/chapters/{chapter_id}"
                    chap_res = await client.get(chapter_detail_url, headers=headers)
                    chap_res.raise_for_status()
                    chapter_detail = chap_res.json()
                    
                    existing_pages = {p["name"]: p["id"] for p in chapter_detail.get("pages", [])}
                    
                    if not os.path.exists(target_dir):
                        continue
                        
                    if target_type in ["rules", "workflows"]:
                        for filename in os.listdir(target_dir):
                            if filename.endswith(".md"):
                                page_name = filename[:-3]
                                local_path = os.path.join(target_dir, filename)
                                rel_path = f".agents/{target_type}/{filename}"
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
                                        
                                    # [NEW] Append other files in skill_dir as fenced code blocks
                                    has_extra = False
                                    for root, _, files in os.walk(skill_dir):
                                        if "__pycache__" in root: continue
                                        for fname in files:
                                            if fname == "SKILL.md" or fname.endswith(".pyc") or fname.startswith("."): continue
                                            fpath = os.path.join(root, fname)
                                            sub_rel = os.path.relpath(fpath, skill_dir)
                                            
                                            try:
                                                with open(fpath, "r", encoding="utf-8") as xf:
                                                    xcontent = xf.read()
                                            except Exception:
                                                continue
                                                
                                            ext = fname.split('.')[-1] if '.' in fname else 'text'
                                            lang_map = {'py': 'python', 'sh': 'bash', 'json': 'json', 'yaml': 'yaml', 'yml': 'yaml', 'md': 'markdown', 'js': 'javascript', 'ts': 'typescript'}
                                            lang = lang_map.get(ext, ext)
                                            
                                            if not has_extra:
                                                content += "\n\n---\n### 🛠️ Scripts & Dependencies\n"
                                                has_extra = True
                                            
                                            content += f"\n````{lang} filepath=\"{sub_rel}\"\n{xcontent}\n````\n"
                                            
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
                                    
                # 4. Update 대상들의 본문 내용을 병렬로 가져와서 변경 여부(Match) 판별
                update_items = [item for item in plan if item["action"] == "Update"]
                
                async def fetch_and_compare(item):
                    page_url = f"{self.api_url}/pages/{item['page_id']}"
                    try:
                        res = await client.get(page_url, headers=headers)
                        res.raise_for_status()
                        remote_markdown = res.json().get("markdown", "")
                        
                        # \r\n 정규화 후 비교
                        if remote_markdown.replace("\r\n", "\n").strip() == item["content"].replace("\r\n", "\n").strip():
                            item["action"] = "Match"
                    except Exception as e:
                        logger.warning(f"Failed to fetch content for comparison: {e}")
                        logger.warning("Upsert Plan 비교 중 페이지 fetch 오류. .artiops.toml 및 글로벌 인증 파일을 확인하세요.")

                if update_items:
                    await asyncio.gather(*(fetch_and_compare(item) for item in update_items))
                    
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
                        logger.info(f"BookStack 페이지 업데이트 완료: {item['name']} (ID: {item['page_id']})")
                except Exception as e:
                    logger.error(f"Failed to {item['action']} page {item['name']}: {e}")
                    logger.error(f"Upsert 실패: {item['name']} (BookStack API 에러)")

