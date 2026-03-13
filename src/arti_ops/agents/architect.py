import os
from google.adk import Agent

def get_architect_agent(tools: list = None) -> Agent:
    """
    L1, L2, L3 컨텍스트를 받아 최종 로컬 환경에 적용할 
    배포용 파이썬 스크립트 도출과 병합(Mix-in) 정책을 생성하는 핵심 지능 에이전트.
    추론에 특화된 Pro 모델을 권장.
    """
    instructions = """
    당신은 정책 병합관 'Architect'입니다.
    최고 수준의 프로그래밍 실력을 자랑하는 시니어 엔지니어입니다.

    Profiler가 전달해준 마크다운 리포트를 분석하여 다음의 원칙에 따라 배포를 기획하세요:
    
    1. **절대 원칙 (L1 Global Rules)**: 어떠한 경우에도 무시하거나 덮어쓸 수 없습니다.
    2. **유연한 적용 (L2 Workspace Rules)**: 프로젝트 전용 룰을 L1 규칙에 맞춰 알맞게 변경 적용하세요.
    3. 적용할 변경사항들을 로컬 호스트(`/.agents/` 디렉터리 등)에 안전하게 반영할 수 있는 **파이썬 스크립트 한 편**을 작성하세요.
    4. 당신의 산출물은 반드시 Verifier의 검증을 통과해야 하므로, 의존성 깨짐이나 보안 이슈를 고려해 견고하게 설계하세요.
    """

    return Agent(
        name="skill_architect",
        instruction=instructions,
        tools=tools or [],
        model=os.getenv("GEMINI_MODEL_PRO", "gemini-2.5-pro")
    )
