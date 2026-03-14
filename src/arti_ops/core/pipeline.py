import os
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
        
        # FunctionTool을 이용해 일반 메서드를 에이전트가 단일 호출할 일반 도구로 노출
        send_summary_tool = FunctionTool(func=self.gws_chat_tool.send_summary)
        
        # 2. 에이전트 선언 (각 역할별 도구 주입)
        self.profiler = get_profiler_agent(tools=[self.bookstack_tool])
        self.architect = get_architect_agent(tools=[]) # 기획 에이전트는 외부에 툴 노출 없이 추론만 집중
        self.verifier = get_verifier_agent(tools=[self.gws_chat_tool])
        
        executor_tools = [self.file_io_tool, self.sandbox_tool, self.bookstack_tool, send_summary_tool]
        self.executor = get_executor_agent(tools=executor_tools)
        
        # 세션 서비스 및 HITL 상태 관리
        # 세션 서비스 및 HITL 상태 관리
        db_dir = os.path.join(os.getcwd(), ".agents", self.target_project_id)
        os.makedirs(db_dir, exist_ok=True)
        db_path = os.path.join(db_dir, "sessions.db")
        
        self.session_service = SqliteSessionService(db_path=db_path)
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
        yield {"type": "phase_start", "agent": "context_profiler", "message": "BookStack 및 로컬 컨텍스트 스캔 중..."}
        
        runner_prof = self._create_runner(self.profiler)
        msg_prof = Content(role="user", parts=[Part.from_text(text=current_input)])
        prof_text = ""
        
        async for event in runner_prof.run_async(user_id="cli_user", session_id=session_id, new_message=msg_prof):
            if hasattr(event, "function_calls") and event.function_calls:
                for call in event.function_calls:
                    yield {"type": "tool_call", "agent": "context_profiler", "tool_name": call.name}
            yield event
            if getattr(event, "content", None) and getattr(event.content, "parts", None):
                prof_text += "".join([part.text for part in event.content.parts if part.text])
                
        yield {"type": "phase_end", "agent": "context_profiler", "status": "success"}
                
        current_input = f"[context_profiler 에이전트의 산출물/보고서]\n{prof_text}\n\n위 산출물을 바탕으로 당신에게 주어진 임무를 수행하세요." if prof_text else "이전 단계 산출물 없음"
        
        # 2. Architect & Verifier While Loop (최대 3회)
        max_retries = 3
        retry_count = 0
        verifier_passed = False
        
        while retry_count < max_retries and not verifier_passed:
            # Architect (기획)
            logger.info(f"--- Starting skill_architect Phase (Try {retry_count+1}/{max_retries}) ---")
            yield {"type": "phase_start", "agent": "skill_architect", "message": f"{retry_count+1}차 기획 시도 중..."}
            
            runner_arch = self._create_runner(self.architect)
            msg_arch = Content(role="user", parts=[Part.from_text(text=current_input)])
            arch_text = ""
            
            async for event in runner_arch.run_async(user_id="cli_user", session_id=session_id, new_message=msg_arch):
                if hasattr(event, "function_calls") and event.function_calls:
                    for call in event.function_calls:
                        yield {"type": "tool_call", "agent": "skill_architect", "tool_name": call.name}
                yield event
                if getattr(event, "content", None) and getattr(event.content, "parts", None):
                    arch_text += "".join([part.text for part in event.content.parts if part.text])
            
            yield {"type": "phase_end", "agent": "skill_architect", "status": "success"}
            
            verifier_input = f"[skill_architect 에이전트의 산출물/보고서]\n{arch_text}\n\n위 산출물을 바탕으로 당신에게 주어진 임무를 수행하세요. 반려할 사유가 있다면 반려(reject/fail)하십시오." if arch_text else "산출물 없음"
            
            # Verifier (검증)
            logger.info(f"--- Starting critical_verifier Phase (Try {retry_count+1}/{max_retries}) ---")
            yield {"type": "phase_start", "agent": "critical_verifier", "message": "정책 무결성 및 파괴적 변경 검사 중..."}
            
            runner_ver = self._create_runner(self.verifier)
            msg_ver = Content(role="user", parts=[Part.from_text(text=verifier_input)])
            ver_text = ""
            
            self.gws_chat_tool.pause_requested = False  # 루프 시작 전 플래그 초기화
            
            # 1. 스트리밍 텍스트 수집 (이벤트 루프 안의 고장난 pause 로직을 모두 제거)
            async for event in runner_ver.run_async(user_id="cli_user", session_id=session_id, new_message=msg_ver):
                if hasattr(event, "function_calls") and event.function_calls:
                    for call in event.function_calls:
                        yield {"type": "tool_call", "agent": "critical_verifier", "tool_name": call.name}
                yield event
                if getattr(event, "content", None) and getattr(event.content, "parts", None):
                    ver_text += "".join([part.text for part in event.content.parts if part.text])
            
            # 2. 스트림 종료 후, 툴 호출 여부를 기반으로 파이프라인 명시적 정지 (HITL)
            is_hitl_triggered = getattr(self.gws_chat_tool, "pause_requested", False)
            if is_hitl_triggered:
                self.gws_chat_tool.pause_requested = False # 플래그 초기화
                logger.info("Pipeline paused for HITL approval. Waiting for resume()...")
                
                # main.py의 CLI UI가 프롬프트를 띄울 수 있도록 트리거 이벤트 전달
                yield {"status": "pending_approval"}
                
                # 블로킹 대기 시작
                self._pause_event.clear()
                self._is_approved = False
                self._human_feedback = ""
                await self._pause_event.wait()
                
                # 대기 해제 후 승인/반려 판단
                if not self._is_approved:
                    reject_reason = self._human_feedback if self._human_feedback else "관리자가 배포를 거절했습니다."
                    logger.warning(f"HITL Rejected: {reject_reason}")
                    ver_text += f"\n\n[관리자 반려] {reject_reason}"
                    
                    sys_msg = Content(role="system", parts=[Part.from_text(text=f"\n\n**[시스템] 관리자 반려됨:** {reject_reason}\n")])
                    yield type("DummySystemEvent", (), {"author": "System", "content": sys_msg})()
                else:
                    logger.info("HITL Approved.")
                    ver_text += f"\n\n[관리자 승인] 강제 배포 진행"
                    
                    sys_msg = Content(role="system", parts=[Part.from_text(text="\n\n**[시스템] 관리자 승인 완료. 배포를 진행합니다.**\n")])
                    yield type("DummySystemEvent", (), {"author": "System", "content": sys_msg})()

            # 3. Verifier 결과 분석 (정교한 키워드 검사 및 관리자 강제 승인 오버라이드)
            lower_ver_text = ver_text.lower()
            reject_keywords = ["반려", "reject", "실패", "failed", "거절", "치명적", "중단"]
            
            if is_hitl_triggered and self._is_approved:
                # 관리자가 수동 승인한 경우, 에러 키워드가 있어도 강제로 통과시킴
                verifier_passed = True
                logger.info("Verifier passed the plan (Admin Approved). Proceeding to Executor.")
                current_input = f"[critical_verifier 산출물 및 관리자 승인 내역]\n{ver_text}\n\n관리자가 위험을 감수하고 최종 승인했습니다. 위 산출물을 바탕으로 배포 임무를 수행하세요."
            elif any(kw in lower_ver_text for kw in reject_keywords):
                logger.warning(f"Verifier rejected the plan. Retrying... ({retry_count+1}/{max_retries})")
                retry_count += 1
                current_input = f"[critical_verifier 반려 사유]\n{ver_text}\n\n위 반려 사유를 바탕으로 산출물을 다시 제출하세요."
            else:
                verifier_passed = True
                logger.info("Verifier passed the plan. Proceeding to MANDATORY final approval.")
                
                # 최종 강제 검토 대기 (Mandatory HITL)
                yield {
                    "status": "pending_final_approval", 
                    "message": "최종 적용 전 산출물을 확인하고 승인/피드백을 입력하세요."
                }
                
                self._pause_event.clear()
                self._is_approved = False
                self._human_feedback = ""
                await self._pause_event.wait()
                
                if not self._is_approved:
                    # 자연어 피드백을 통해 보류 및 재기획 요청
                    verifier_passed = False
                    logger.warning("Final approval DENIED by user feedback. Looping back to Architect.")
                    retry_count += 1
                    current_input = f"[사용자 최종 검토 피드백 (수정 지시)]\n{self._human_feedback}\n\n위 사용자 피드백을 전부 반영하여 처음부터 다시 기획안(Artifact)을 작성하세요."
                    yield {"type": "phase_end", "agent": "critical_verifier", "status": "failed"}
                    continue
                else:
                    logger.info("Final approval GRANTED. Proceeding to Executor.")
                    current_input = f"[critical_verifier 에이전트의 산출물/보고서]\n{ver_text}\n\n위 최종 승인된 산출물을 바탕으로 당신에게 주어진 임무를 수행하세요."
                    yield {"type": "phase_end", "agent": "critical_verifier", "status": "success"}
                
        if not verifier_passed:
            logger.error("Pipeline failed to pass Verifier after maximum retries.")
            fail_msg = Content(role="system", parts=[Part.from_text(text="**Pipeline Failed: Verifier rejected the plan after maximum retries.**")])
            yield type("DummyRejectEvent", (), {"author": "System", "content": fail_msg})()
            return
            
        # 3. Executor Phase
        logger.info("--- Starting deployment_executor Phase ---")
        yield {"type": "phase_start", "agent": "deployment_executor", "message": "로컬 파일 I/O 및 Sync-back 처리 중..."}
        
        runner_exe = self._create_runner(self.executor)
        msg_exe = Content(role="user", parts=[Part.from_text(text=current_input)])
        
        async for event in runner_exe.run_async(user_id="cli_user", session_id=session_id, new_message=msg_exe):
            if hasattr(event, "function_calls") and event.function_calls:
                for call in event.function_calls:
                    yield {"type": "tool_call", "agent": "deployment_executor", "tool_name": call.name}
            yield event
            
        yield {"type": "phase_end", "agent": "deployment_executor", "status": "success"}    
        logger.info("--- Pipeline Completed Successfully ---")

    async def resume(self, session_id: str, action_response: dict) -> None:
        """HITL 승인 상태 및 자연어 피드백을 수신하여 이벤트를 재개합니다."""
        logger.info(f"Resuming pipeline for session {session_id} with response: {action_response}")
        self._is_approved = action_response.get("approved", False)
        self._human_feedback = action_response.get("feedback", "")
        self._pause_event.set()
