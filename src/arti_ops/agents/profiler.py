import os
from google.adk.agents import Agent
from arti_ops.config import get_config

def get_profiler_agent(tools: list = None) -> Agent:
    instructions = """
    당신은 사용자 의도를 분석하여 배포 대상 파일 목록(Target Files)을 추출하는 'Context Profiler'입니다.
    사용자의 지시사항을 분석하여, 수정이나 확장이 필요한 **로컬 파일 경로(.agents/...)**를 리스트화하십시오.
    1. 새 룰셋이 필요한 경우 `write_file` 등을 위한 경로 리스트업.
    2. 기존 규칙이 존재할 경우 반드시 `read_file`로 먼저 읽어들일 대상 포함.
    """
    return Agent(name="context_profiler", instruction=instructions, tools=tools or [], model=get_config("GEMINI_MODEL_FLASH", "gemini-2.5-flash"))
