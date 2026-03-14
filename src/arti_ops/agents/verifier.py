import os
from google.adk import Agent

def get_verifier_agent(tools: list = None) -> Agent:
    """
    Architect가 생성한 배포 산출물을 Red-Team 관점에서 검증하는 에이전트.
    Global 정책(L1) 위반 여부나 파괴적 변경을 탐지합니다.
    자체 해결 불가능한 충돌 감지 시 (Pause) HITL Tool 인 GwsChatTool을 호출합니다.
    """
    instructions = """
    당신은 깐깐한 감사관 'Verifier' (Red-Team)입니다.
    
    1. Architect 에이전트가 만든 산출물(리팩토링 된 배포 스크립트나 정책 파일 등)에 L1 Global Rule을 조금이라도 위반하는 내용이 있는지 심사하세요.
    2. 로컬 의존성 구조를 망가뜨리거나 기존 파일을 위험하게 덮어쓰는지 체크하세요.
    3. 만약 위반 사항이 있거나 경미한 오류라면, 그 사유를 반환하여 루프(Self-Correction)가 Architect에게 재작업을 지시하도록 유도하세요.
    4. 검증 결과 문제가 없다면, TUI 화면에 출력될 수 있도록 "반영될 파일들의 정확한 이름, 경로, 그리고 전체 코드 내용을 사용자가 한눈에 읽을 수 있도록 깔끔하게 포맷팅한 [최종 검토용 상세 보고서]"를 산출물로 제출하세요. (이 보고서는 샌드박스 실행이나 GWS 호출 없이, 오직 TUI 렌더링용 마크다운 형식이어야 합니다.)
    """

    return Agent(
        name="critical_verifier",
        instruction=instructions,
        tools=tools or [],
        model=os.getenv("GEMINI_MODEL_PRO", "gemini-2.5-pro")
    )
