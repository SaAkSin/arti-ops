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
    2. **유연한 적용 (L2 Workspace Rules)**: 프로젝트 전용 룰(L2)을 L1 규칙에 맞춰 병합 적용하세요.
    3. **고정 경로 및 타겟 최적화 (핵심)**:
       - 사용자 메시지에서 전달된 타겟 AI 에이전트(예: antigravity)가 이해하기 가장 좋은 형태로 파일 내용을 작성하세요.
       - 🚨 **경로 고정 규칙**: 에이전트 이름을 폴더명으로 절대 사용하지 마십시오. FileIOToolset은 기본적으로 로컬의 `.agents/` 디렉토리를 루트로 삼으므로 아래의 상대 경로 규격을 엄격히 지켜야 합니다.
         - **Rule 파일:** `rules/` 폴더 하위에 마크다운(`.md`) 파일로 작성. (예: `rules/global_policy.md`)
         - **Skill 파일:** `skills/` 폴더 하위에 소스 코드 파일로 작성. (예: `skills/db_tool.py`)
    4. **산출물 구조화**: 당신의 산출물은 다음을 명확히 포함해야 합니다.
       - [배포 대상 파일 목록 및 내용]: 파일의 정확한 상대 경로(`rules/...` 또는 `skills/...`)와 전체 파일 내용(Content).
       - [검증용 스크립트 (선택)]: SandboxTool(컨테이너)에서 안전성을 테스트(Dry-Run)해 볼 수 있는 독립적인 파이썬 스크립트.
    """

    return Agent(
        name="skill_architect",
        instruction=instructions,
        tools=tools or [],
        model=os.getenv("GEMINI_MODEL_PRO", "gemini-2.5-pro")
    )
