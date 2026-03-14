import os
from google.adk.agents import Agent
from arti_ops.config import get_config
from arti_ops.config import get_config

def get_executor_agent(tools: list = None) -> Agent:
    instructions = """
    당신은 배포 집행관 'Executor'입니다. 사용자 승인을 거친 기획안을 전달 받았습니다.
    1. **실제 파일 배포**: `FileIOToolset`의 `write_file` 도구를 호출하여 기획안에 명시된 경로(`.agents/...`)에 파일들을 로컬 호스트에 즉시 생성하십시오.
    2. **최종 요약 보고**: 모든 파일 배포가 끝나면, 단 1회 `send_summary` 도구를 호출하여 '어떤 파일들이 반영되었는지'에 대한 요약 보고서를 GWS 채팅방으로 전송하십시오.
    """
    return Agent(name="deployment_executor", instruction=instructions, tools=tools or [], model=get_config("GEMINI_MODEL_FLASH", "gemini-2.5-flash"))
