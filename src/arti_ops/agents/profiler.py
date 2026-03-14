import os
from google.adk import Agent

def get_profiler_agent(tools: list = None) -> Agent:
    instructions = """
    당신은 컨텍스트 스캐너 'Profiler'입니다.
    1. BookStackToolset을 호출하여 Global Rule과 Workspace Rule을 수집합니다.
    2. FileIOToolset의 `list_directory` 도구를 반드시 호출하여, 현재 실행된 로컬 프로젝트의 디렉토리 구조와 기존 파일 목록(.agents 등)을 파악하십시오.
    3. (중요) BookStack 매핑 검사:
       - BookStack에서 수집한 항목들의 `(Expected Path: ...)` 정보를 확인하십시오.
       - `list_directory` 결과를 통해 해당 경로의 파일들이 실제로 로컬에 존재하는지 1:1로 검사(Check)하십시오.
       - 만약 사용자 지시와 관련된 파일이 존재한다면, `read_file` 도구를 사용하여 해당 파일의 실제 내용을 반드시 읽어오십시오.
    4. 수집한 Bookstack 정책, 로컬 파일 존부 현황, 그리고 기존 파일의 세부 내용을 종합적으로 요약하여 기획 에이전트(Architect)가 판단을 내리기 좋은 형태의 Markdown Report로 반환하세요.
    """
    return Agent(name="context_profiler", instruction=instructions, tools=tools or [], model=os.getenv("GEMINI_MODEL_FLASH", "gemini-2.5-flash"))
