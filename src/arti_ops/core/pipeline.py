import os
import asyncio
import logging
from typing import AsyncGenerator
from google.adk import Runner, Agent
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part

from ..agents.profiler import get_profiler_agent
from ..agents.architect import get_architect_agent
from ..agents.verifier import get_verifier_agent
from ..agents.executor import get_executor_agent

from ..tools.bookstack import BookStackToolset
from ..tools.gws_chat import GwsChatTool
from ..tools.sandbox import SandboxTool
from ..tools.file_io import FileIOToolset

logger = logging.getLogger(__name__)

class ArtiOpsPipeline:
    def __init__(self, target_project_id: str):
        self.target_project_id = target_project_id
        
        # 1. 툴 선언
        self.bookstack_tool = BookStackToolset()
        self.file_io_tool = FileIOToolset()
        self.sandbox_tool = SandboxTool()
        self.gws_chat_tool = GwsChatTool()
        
        # 2. 에이전트 선언 (각 역할별 도구 주입)
        self.profiler = get_profiler_agent(tools=[self.bookstack_tool])
        self.architect = get_architect_agent(tools=[]) # 기획 에이전트는 외부에 툴 노출 없이 추론만 집중
        self.verifier = get_verifier_agent(tools=[self.gws_chat_tool])
        self.executor = get_executor_agent(tools=[self.file_io_tool, self.sandbox_tool, self.bookstack_tool])
        
        # 세션 서비스 및 HITL 상태 관리
        self.session_service = InMemorySessionService()
        self._pause_event = asyncio.Event()
        self._is_approved = False
        self._human_feedback = "" # 🚨 신규 추가: 피드백 저장용 문자열

    def _create_runner(self, agent: Agent) -> Runner:
        return Runner(
            app_name=f"arti-ops-{agent.name}",
            agent=agent,
            session_service=self.session_service,
            auto_create_session=True
        )

    async def run(self, command_prompt: str, session_id: str = None) -> AsyncGenerator[any, None]:
        """
        초기 프롬프트를 전송하여 파이프라인(Profiler -> [Architect -> Verifier] -> Executor)을 실행시킵니다.
        """
        session_id = session_id or f"sess_{self.target_project_id}"
        current_input = command_prompt
        
        # 1. Profiler Phase (단일 실행)
        logger.info("--- Starting context_profiler Phase ---")
        runner_prof = self._create_runner(self.profiler)
        msg_prof = Content(role="user", parts=[Part.from_text(text=current_input)])
        prof_text = ""
        
        async for event in runner_prof.run_async(user_id="cli_user", session_id=session_id, new_message=msg_prof):
            yield event
            if getattr(event, "content", None) and getattr(event.content, "parts", None):
                prof_text += "".join([part.text for part in event.content.parts if part.text])
                
        current_input = f"[context_profiler 에이전트의 산출물/보고서]\n{prof_text}\n\n위 산출물을 바탕으로 당신에게 주어진 임무를 수행하세요." if prof_text else "이전 단계 산출물 없음"
        
        # 2. Architect & Verifier While Loop (최대 3회)
        max_retries = 3
        retry_count = 0
        verifier_passed = False
        
        while retry_count < max_retries and not verifier_passed:
            # Architect (기획)
            logger.info(f"--- Starting skill_architect Phase (Try {retry_count+1}/{max_retries}) ---")
            runner_arch = self._create_runner(self.architect)
            msg_arch = Content(role="user", parts=[Part.from_text(text=current_input)])
            arch_text = ""
            
            async for event in runner_arch.run_async(user_id="cli_user", session_id=session_id, new_message=msg_arch):
                yield event
                if getattr(event, "content", None) and getattr(event.content, "parts", None):
                    arch_text += "".join([part.text for part in event.content.parts if part.text])
            
            verifier_input = f"[skill_architect 에이전트의 산출물/보고서]\n{arch_text}\n\n위 산출물을 바탕으로 당신에게 주어진 임무를 수행하세요. 반려할 사유가 있다면 반려(reject/fail)하십시오." if arch_text else "산출물 없음"
            
            # Verifier (검증)
            logger.info(f"--- Starting critical_verifier Phase (Try {retry_count+1}/{max_retries}) ---")
            runner_ver = self._create_runner(self.verifier)
            msg_ver = Content(role="user", parts=[Part.from_text(text=verifier_input)])
            ver_text = ""
            
            async for event in runner_ver.run_async(user_id="cli_user", session_id=session_id, new_message=msg_ver):
                yield event
                
                # 중단(Pause) 이벤트(HITL) 감지
                is_paused = False
                if isinstance(event, dict) and event.get("status") == "pending_approval":
                    is_paused = True
                elif getattr(event, "__class__", None) and getattr(event.__class__, "__name__", "") == "PauseEvent":
                    is_paused = True
                    
                if is_paused:
                    logger.info("Pipeline paused for HITL approval. Waiting for resume()...")
                    self._pause_event.clear()
                    self._is_approved = False
                    self._human_feedback = ""
                    await self._pause_event.wait()
                    
                    if not self._is_approved:
                        reject_reason = self._human_feedback if self._human_feedback else "인간 관리자가 배포를 단순 반려했습니다."
                        # "반려" 키워드를 넣어 하단 루프의 재시도(Retry) 조건이 발동되게 유도함
                        ver_text += f"\n\n[Human Review 반려됨] 추가 피드백 지시사항: {reject_reason}"
                        reject_msg = Content(role="system", parts=[Part.from_text(text=f"**Human rejected.** Reason/Feedback: {reject_reason}")])
                        yield type("DummyRejectEvent", (), {"author": "System", "content": reject_msg})()
                    else:
                        ver_text += "\n\n[Human Review] 승인됨."
                        approve_msg = Content(role="system", parts=[Part.from_text(text="**Human reviewer approved. Resuming...**")])
                        yield type("DummyApproveEvent", (), {"author": "System", "content": approve_msg})()
                    continue

                if getattr(event, "content", None) and getattr(event.content, "parts", None):
                    ver_text += "".join([part.text for part in event.content.parts if part.text])
            
            # Verifier 결과 분석 (간단한 키워드 기반)
            lower_ver_text = ver_text.lower()
            if "반려" in lower_ver_text or "reject" in lower_ver_text or "실패" in lower_ver_text or "failed" in lower_ver_text:
                logger.warning(f"Verifier rejected the plan. Retrying... ({retry_count+1}/{max_retries})")
                retry_count += 1
                current_input = f"[critical_verifier 에이전트의 피드백 (반려 사유)]\n{ver_text}\n\n위 피드백(오류/반려 사유)을 바탕으로 기존 코드를 수정/보완하는 산출물을 다시 제출하세요."
            else:
                verifier_passed = True
                logger.info("Verifier passed the plan. Proceeding to Executor.")
                current_input = f"[critical_verifier 에이전트의 산출물/보고서]\n{ver_text}\n\n위 산출물을 바탕으로 당신에게 주어진 임무를 수행하세요."
                
        if not verifier_passed:
            logger.error("Pipeline failed to pass Verifier after maximum retries.")
            fail_msg = Content(role="system", parts=[Part.from_text(text="**Pipeline Failed: Verifier rejected the plan after maximum retries.**")])
            yield type("DummyRejectEvent", (), {"author": "System", "content": fail_msg})()
            return
            
        # 3. Executor Phase
        logger.info("--- Starting deployment_executor Phase ---")
        runner_exe = self._create_runner(self.executor)
        msg_exe = Content(role="user", parts=[Part.from_text(text=current_input)])
        
        async for event in runner_exe.run_async(user_id="cli_user", session_id=session_id, new_message=msg_exe):
            yield event
            
        logger.info("--- Pipeline Completed Successfully ---")

    async def resume(self, session_id: str, action_response: dict) -> None:
        """HITL 승인 상태 및 자연어 피드백을 수신하여 이벤트를 재개합니다."""
        logger.info(f"Resuming pipeline for session {session_id} with response: {action_response}")
        self._is_approved = action_response.get("approved", False)
        self._human_feedback = action_response.get("feedback", "")
        self._pause_event.set()
