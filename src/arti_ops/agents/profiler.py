import os
from google.adk import Agent

def get_profiler_agent(tools: list = None) -> Agent:
    """
    BookStack 서버와 로컬 환경을 조회하여 융합 컨텍스트를 설계하는 Profiler 에이전트.
    주로 빠르고 경제적인 처리(Flash 모델)를 권장합니다.
    """
    instructions = """
    당신은 컨텍스트 스캐너 'Profiler'입니다.
    
    1. 현재 BookStackToolset을 호출하여 Global Rule (L1)과 Project Workspace Rule (L2)을 수집합니다.
    2. 제공된 툴(FileIOToolset 등)을 사용하여, **명령어가 실행된 현재 로컬 디렉토리(`os.getcwd()`)의 주요 소스코드 파일 및 작성물들(특히 `.agents/` 디렉토리 하위의 내용 등)**을 스캔하여 컨텍스트로 수집하십시오.
    3. 수집한 BookStack 정책과 로컬 시스템의 구조/코드 현황을 종합적으로 병합하고 요약하여, 기획 에이전트(Architect)가 참고하기 가장 좋은 형태의 Markdown Report로 반환하세요.
    """

    return Agent(
        name="context_profiler",
        instruction=instructions,
        tools=tools or [],
        model=os.getenv("GEMINI_MODEL_FLASH", "gemini-2.5-flash")
    )
