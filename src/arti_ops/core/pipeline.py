import os
import re
import asyncio
import logging
from typing import AsyncGenerator
from google.adk import Runner, Agent
from google.adk.tools import FunctionTool
from google.adk.sessions.sqlite_session_service import SqliteSessionService
from google.genai.types import Content, Part

from ..agents.profiler import get_profiler_agent
from ..agents.architect import get_architect_agent
from ..agents.verifier import get_verifier_agent
from ..agents.executor import get_executor_agent

from ..tools.bookstack import BookStackToolset
from ..tools.gws_chat import GwsChatTool
from ..tools.file_io import FileIOToolset

logger = logging.getLogger(__name__)

class ArtiOpsPipeline:
    def __init__(self, target_project_id: str):
        self.target_project_id = target_project_id
        
        self.ui_queue = asyncio.Queue()
        BookStackToolset.set_ui_queue(self.ui_queue)
        from ..tools.file_io import FileIOToolset
        FileIOToolset.set_ui_queue(self.ui_queue)
        
        # 1. 툴 선언 (SandboxTool 제거됨)
        self.bookstack_tool = BookStackToolset()
        self.file_io_tool = FileIOToolset()
        self.gws_chat_tool = GwsChatTool()
        send_summary_tool = FunctionTool(func=self.gws_chat_tool.send_summary)
        
        # 2. 에이전트 선언 (Profiler에 로컬 스캔 권한 부여)
        self.profiler = get_profiler_agent(tools=[self.bookstack_tool, self.file_io_tool])
        self.architect = get_architect_agent(tools=[]) 
        self.verifier = get_verifier_agent(tools=[])
        self.executor = get_executor_agent(tools=[self.file_io_tool, self.bookstack_tool, send_summary_tool])
        
        from arti_ops.config import Configurator
        config = Configurator.get_instance()
        # 세션 서비스 설정: Global DB 사용 (session_id 로 구분됨)
        db_path = str(os.path.expanduser("~/.arti-ops/arti_ops_session.db"))
        self.session_service = SqliteSessionService(db_path=db_path)
        
        self._pause_event = asyncio.Event()
        self._is_approved = False
        self._human_feedback = ""

    def _create_runner(self, agent: Agent) -> Runner:
        return Runner(
            app_name=f"arti-ops-{agent.name}",
            agent=agent,
            session_service=self.session_service,
            auto_create_session=True
        )

    async def run(self, command_prompt: str, session_id: str = None) -> AsyncGenerator[any, None]:
        session_id = session_id or f"sess_{self.target_project_id}"
        current_input = command_prompt
        
        async def pump_runner(runner, **kwargs):
            try:
                async for e in runner.run_async(**kwargs):
                    await self.ui_queue.put({"type": "runner_event", "data": e})
            finally:
                await self.ui_queue.put({"type": "runner_done"})

        # [1] Profiler Phase
        yield {"type": "phase_start", "agent": "context_profiler", "message": "로컬 파일 구조 및 위키 정책 수집 중..."}
        runner_prof = self._create_runner(self.profiler)
        prof_text = ""
        tool_called = False
        
        asyncio.create_task(pump_runner(runner_prof, user_id="cli_user", session_id=session_id, new_message=Content(role="user", parts=[Part.from_text(text=current_input)])))
        
        while True:
            q_evt = await self.ui_queue.get()
            import logging
            logging.getLogger(__name__).info(f"====== [DEBUG PIPELINE] Pulled from ui_queue: {q_evt['type']} ======")
            
            if q_evt["type"] == "runner_done":
                break
            elif q_evt["type"] == "ui_message":
                tool_called = True
                logging.getLogger(__name__).info(f"====== [DEBUG PIPELINE] Yielding UI message: {q_evt['data']} ======")
                yield q_evt["data"]
            elif q_evt["type"] == "runner_event":
                event = q_evt["data"]
                if hasattr(event, "function_calls") and event.function_calls:
                    for call in event.function_calls:
                        tool_called = True
                        yield {"type": "tool_call", "agent": "context_profiler", "tool_name": call.name}
                if getattr(event, "content", None) and event.content.parts:
                    prof_text += "".join([p.text for p in event.content.parts if p.text])
                
        if not tool_called and prof_text.strip():
            yield {
                "type": "subnode_add",
                "agent": "context_profiler",
                "message": "💡 이전 세션(sessions.db) 기억을 불러왔습니다.",
                "color": "magenta"
            }
            
        yield {"type": "phase_end", "agent": "context_profiler", "status": "success"}
        current_input = f"[Profiler 컨텍스트 보고서]\n{prof_text}\n\n위 내용을 참고하여 사용자의 초기 지시를 완수하세요." if prof_text else current_input
        
        # [2] Architect & Verifier Loop
        max_retries = 3
        retry_count = 0
        verifier_passed = False
        
        while retry_count < max_retries and not verifier_passed:
            # Architect Phase
            yield {"type": "phase_start", "agent": "skill_architect", "message": f"{retry_count+1}차 맞춤형 스킬/룰 기획 중..."}
            runner_arch = self._create_runner(self.architect)
            arch_text = ""
            reported_paths = set()
            
            async for event in runner_arch.run_async(user_id="cli_user", session_id=session_id, new_message=Content(role="user", parts=[Part.from_text(text=current_input)])):
                if getattr(event, "content", None) and event.content.parts:
                    chunk = "".join([p.text for p in event.content.parts if p.text])
                    arch_text += chunk
                    
                    # 실시간 파싱: .agents/rules/xxx.md 또는 .agents/skills/xxx/SKILL.md 경로 감지
                    matches = re.findall(r'(\.agents/(?:rules|skills)/[\w\-\./]+\.md)', arch_text)
                    for match in matches:
                        if match not in reported_paths:
                            reported_paths.add(match)
                            yield {
                                "type": "subnode_add",
                                "agent": "skill_architect",
                                "message": f"📝 기획 타겟: {match}",
                                "color": "yellow"
                            }
                            
            yield {"type": "phase_end", "agent": "skill_architect", "status": "success"}
            
            # Verifier Phase
            yield {"type": "phase_start", "agent": "critical_verifier", "message": "정책 무결성 검증 및 최종 보고서 작성 중..."}
            runner_ver = self._create_runner(self.verifier)
            ver_text = ""
            
            async for event in runner_ver.run_async(user_id="cli_user", session_id=session_id, new_message=Content(role="user", parts=[Part.from_text(text=f"[Architect 기획안]\n{arch_text}\n\n검증 후 최종 보고서를 작성하세요.")])):
                if getattr(event, "content", None) and event.content.parts:
                    ver_text += "".join([p.text for p in event.content.parts if p.text])

            # 실패 키워드 검사 (너무 단순한 키워드 매칭은 생성된 본문 내용에 걸려 오탐рит될 수 있으므로, 검토 결과 섹션에 한정하거나 더 명시적인 표현을 찾도록 완화합니다.)
            is_rejected = False
            # 첫 부분이나 전체적인 맥락에서 '승인 거절', '검토 실패', '반려합니다' 등 노골적인 거부 의사가 있는지 확인. 본문에 포함된 단순 단어는 무시.
            fail_phrases = ["검토 결과: 반려", "검토 결과: 실패", "결과: 반려", "결과: 실패", "승인 거부", "승인 불가"]
            if any(kw in ver_text for kw in fail_phrases):
                is_rejected = True
                
            if is_rejected:
                retry_count += 1
                current_input = f"[Verifier 반려 사유]\n{ver_text}\n\n위 반려 사유를 바탕으로 산출물을 수정하여 재기획하세요."
                yield {"type": "phase_end", "agent": "critical_verifier", "status": "failed"}
            else:
                yield {"type": "phase_end", "agent": "critical_verifier", "status": "success"}
                # 최종 강제 검토 대기 (Mandatory HITL)
                self._pause_event.clear()
                yield {
                    "status": "pending_final_approval", 
                    "report": ver_text
                }
                
                await self._pause_event.wait()
                
                if not self._is_approved:
                    verifier_passed = False
                    retry_count += 1
                    current_input = f"[사용자 피드백 (수정 지시)]\n{self._human_feedback}\n\n위 사용자 피드백을 전부 반영하여 기획안을 다시 작성하세요."
                    continue
                else:
                    verifier_passed = True
                    current_input = f"[최종 승인된 기획안 (원본 코드)]\n{arch_text}\n\n[검증 결과 요약]\n{ver_text}\n\n위 승인된 기획안(원본 코드)의 내용을 바탕으로 로컬 파일 쓰기(`write_file` 도구 사용)를 수행하세요. 파일 생성 시 내용(content) 인자에는 요약문이 아닌 원본 마크다운/코드 전체가 반드시 포함되어야 합니다."
                
        if not verifier_passed:
            return
            
        # [3] Executor Phase
        yield {"type": "phase_start", "agent": "deployment_executor", "message": "실제 로컬 파일 I/O 배포 진행 중..."}
        runner_exe = self._create_runner(self.executor)
        
        async for event in runner_exe.run_async(user_id="cli_user", session_id=session_id, new_message=Content(role="user", parts=[Part.from_text(text=current_input)])):
            if hasattr(event, "function_calls") and event.function_calls:
                for call in event.function_calls:
                    yield {"type": "tool_call", "agent": "deployment_executor", "tool_name": call.name}
                    
        yield {"type": "phase_end", "agent": "deployment_executor", "status": "success"}

    async def resume(self, session_id: str, action_response: dict) -> None:
        self._is_approved = action_response.get("approved", False)
        self._human_feedback = action_response.get("feedback", "")
        self._pause_event.set()
