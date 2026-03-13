import os
from google.adk import Agent

def get_profiler_agent() -> Agent:
    """
    BookStack 서버와 로컬 환경을 조회하여 융합 컨텍스트를 설계하는 Profiler 에이전트.
    주로 빠르고 경제적인 처리(Flash 모델)를 권장합니다.
    """
    instructions = """
    당신은 컨텍스트 스캐너 'Profiler'입니다.
    
    1. 현재 BookStackToolset을 호출하여 Global Rule (L1)과 Project Workspace Rule (L2)을 수집합니다.
    2. 로컬 디렉토리 환경과 이전 버전 정책 현황을 수집합니다.
    3. 수집한 모든 정보들을 요약하고 병합 아키텍트가 참고하기 쉬운 형태의 Markdown Report로 요약하여 반환하세요.
    """

    return Agent(
        name="context_profiler",
        instruction=instructions,
        model=os.getenv("GEMINI_MODEL_FLASH", "gemini-2.5-flash")
    )
