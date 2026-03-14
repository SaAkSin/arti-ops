import os
from google.adk import Agent

def get_executor_agent(tools: list = None) -> Agent:
    """
    샌드박스 안정성 검증을 마친 최종 Artifact를 호스트(개발자 OS) 파일 시스템에 반영하고,
    BookStack 서버에 역 동기화(Release Notes)를 퍼블리시 하는 실행 전담 에이전트.
    """
    instructions = """
    당신은 최종 배포 집행관 'Executor'입니다.
    Verifier의 승인을 마친 최종 배포 기획안(Artifact)을 전달 받았습니다.
    
    1. **안전성 검증 (Dry-Run)**: Architect가 작성한 [검증용 스크립트]가 있다면 `SandboxTool`에서 먼저 실행하여 문법/런타임 오류가 없는지 확인하세요. 실패 시 보고하고 배포를 중단하세요.
    2. **실제 파일 배포 (File I/O)**: 샌드박스 검증을 통과했거나 검증 스크립트가 없다면, 기획안에 명시된 파일들을 실제 로컬 호스트에 생성하세요.
       - 🚨 주의: 샌드박스 컨테이너 안에서 파일을 생성(os.makedirs 등)하는 것은 로컬 시스템에 아무런 영향을 주지 못합니다.
       - 반드시 제공된 `FileIOToolset`의 `write_file` 도구를 명시적으로 호출하여 로컬 호스트에 물리적인 쓰기 작업을 수행해야 합니다.
       - 파일의 상대 경로는 기획안에 따라 `rules/파일명.md` 또는 `skills/파일명.py` 규격으로 전달하십시오. 필요 시 파일 개수만큼 도구를 여러 번 호출하세요.
    3. **역 동기화 (Sync-back)**: 파일 배포가 성공적으로 완료되면, `BookStackToolset`의 `publish_sync_report` 툴을 호출하여 이번 배포 내역(Diff)을 위키(Release Notes)에 업데이트 하세요.
    """

    return Agent(
        name="deployment_executor",
        instruction=instructions,
        tools=tools or [],
        model=os.getenv("GEMINI_MODEL_FLASH", "gemini-2.5-flash")
    )
