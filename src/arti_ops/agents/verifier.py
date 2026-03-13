import os
from google.adk import Agent

def get_verifier_agent() -> Agent:
    """
    Architect가 생성한 배포 산출물을 Red-Team 관점에서 검증하는 에이전트.
    Global 정책(L1) 위반 여부나 파괴적 변경을 탐지합니다.
    자체 해결 불가능한 충돌 감지 시 (Pause) HITL Tool 인 GwsChatTool을 호출합니다.
    """
    instructions = """
    당신은 깐깐한 감사관 'Verifier' (Red-Team)입니다.
    
    1. Architect 에이전트가 만든 산출물(리팩토링 된 Python 배포 스크립트 등)에 L1 Global Rule을 조금이라도 위반하는 내용이 있는지 심사하세요.
    2. 로컬 의존성 구조를 망가뜨리거나 기존 파일을 위험하게 덮어쓰는지 체크하세요.
    3. 만약 위반 사항이 있거나 경미한 오류라면, 그 사유를 반환하여 루프(Self-Correction)가 Architect에게 재작업을 지시하도록 유도하세요.
    4. 당신이 판단하기에 '이건 사람이 직접 결정해야 하는 논란의 여지가 있다' 거나 '위험도가 너무 높은 변경'이라고 생각되면 즉시 `GwsChatTool` 을 호출하여 PM의 승인을 대기하도록 만드세요.
    """

    return Agent(
        name="critical_verifier",
        instruction=instructions,
        model=os.getenv("GEMINI_MODEL_PRO", "gemini-2.5-pro")
    )
