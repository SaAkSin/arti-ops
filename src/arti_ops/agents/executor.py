from google.adk.agent import Agent

def get_executor_agent() -> Agent:
    """
    샌드박스 안정성 검증을 마친 최종 Artifact를 호스트(개발자 OS) 파일 시스템에 반영하고,
    BookStack 서버에 역 동기화(Release Notes)를 퍼블리시 하는 실행 전담 에이전트.
    """
    instructions = """
    당신은 최종 배포 집행관 'Executor'입니다.
    Verifier의 승인을 마친 최종 배포 아티팩트를 당신이 전달 받았습니다.
    
    1. 이 스크립트를 먼저 SandboxTool 의 가상 환경(Container)에서 Dry-Run 구동하여 문법 오류나 런타임 크래쉬가 없는지 1차로 확인하세요.
    2. Sandbox 검증에 실패 시 그 결과를 그대로 보고하여 파이프라인이 중단되게 하세요.
    3. 테스트를 정상 통과 했다면, 생성된 `.agents/` 등 로컬 파일들을 쓰기(File I/O) 하세요.
    4. 최종적으로 BookStackToolset의 `publish_sync_report` 툴을 호출하여 이번에 성공적으로 병합 배포된 내역(Diff)들을 프로젝트 위키에 업데이트 하세요.
    """

    return Agent(
        id="executor",
        name="Deployment Executor",
        instructions=instructions,
        tools=["SandboxTool", "BookStackToolset"]
    )
