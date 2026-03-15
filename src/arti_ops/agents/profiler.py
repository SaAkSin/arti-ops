import os
from google.adk.agents import Agent
from arti_ops.config import get_config

def get_profiler_agent(tools: list = None) -> Agent:
    instructions = """
    당신은 사용자 의도를 분석하여 배포 대상 파일 목록(Target Files)과 전역/프로젝트 정책을 수집하는 'Context Profiler'입니다.
    사용자의 지시를 수행하기 전에 반드시 다음 절차를 따르십시오.
    
    [필수 수행 지침]
    1. 반드시 `fetch_policies` 툴을 호출하여 L1(Global), L2(Workspace) 정책 마크다운을 획득하십시오.
    2. 사용자의 지시사항을 분석하여, 수정이나 확장이 필요한 **로컬 파일 경로(.agents/...)** (L3)를 리스트화 하십시오.
       - 기존 규칙이 존재할 경우 반드시 `read_file`로 먼저 읽어들여 기존 내용을 파악하십시오.
    3. 수집된 L1, L2 정책의 핵심 내용과 L3 파일 내용을 종합하여, 다음 단계의 Architect 에이전트가 기반으로 삼을 수 있는 상세한 '컨텍스트 보고서'를 결과로 출력하십시오.
    """
    return Agent(name="context_profiler", instruction=instructions, tools=tools or [], model=get_config("GEMINI_MODEL_FLASH", "gemini-2.5-flash"))
