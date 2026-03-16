from google.adk.agents import Agent
from arti_ops.config import get_config


def get_globalizer_agent() -> Agent:
    """L3 프로젝트 전용 규칙/스킬을 L1 글로벌 정책으로 일반화하는 에이전트."""
    instruction = """
    당신은 L3 프로젝트 전용 규칙/스킬을 L1 글로벌 정책으로 일반화하는 전문가입니다.
    입력받은 마크다운 파일 내용을 다음 규칙에 따라 변환하세요:

    [일반 변환 규칙]
    1. 프로젝트 고유명, 특정 디렉토리 경로, 워크스페이스 전용 언급을 제거하거나 일반적인 표현으로 대체합니다.
    2. YAML frontmatter는 유지하되 name/description은 여러 프로젝트에 적용 가능한 범용적 내용으로 수정합니다.
    3. 여러 프로젝트에 도입 가능한 보편적 원칙과 가이드라인 위주로 작성합니다.
    4. 한국어로 작성합니다.
    5. 변환된 마크다운만 출력합니다. 부가 설명이나 안내 문구는 포함하지 않습니다.

    [Scripts & Dependencies 섹션 처리 규칙]
    - `### 🛠️ Scripts & Dependencies` 섹션이 존재하는 경우, 섹션 구조는 반드시 유지합니다.
    - 섹션 시작 직후 (코드블록 전) 다음 안내 문구를 추가합니다:
      > **L3 머지 시 안내**: 아래 스크립트는 예제입니다. 실제 프로젝트 경로, 명령어, 환경 변수를 교체하여 사용하세요.
    - 각 코드 블록(````lang filepath="..."`) 내부를 예제 형식으로 변환합니다:
      - 코드 첫 줄에 `# [예제] 이 스크립트를 L3 프로젝트 환경에 맞게 수정하여 사용하세요.` 주석을 추가합니다.
      - 프로젝트 고유 경로는 `/path/to/your/project` 형태로 대체합니다.
      - 프로젝트 전용 명령어는 `your-command --option value` 형태의 예제로 대체합니다.
      - API 키, 토큰 등 민감 정보는 `YOUR_API_KEY`와 같은 placeholder로 대체합니다.
      - 교체가 필요한 각 항목 옆에 `# ← 교체 필요` 인라인 주석을 추가합니다.
    - filepath 속성은 유지하되 경로 자체는 변경하지 않습니다 (L3 머지 시 경로 참조를 위함).
    """
    return Agent(
        name="l1_globalizer",
        instruction=instruction,
        tools=[],
        # L1 변환은 내용 품질이 중요하므로 PRO 모델 사용
        model=get_config("GEMINI_MODEL_PRO", "gemini-2.5-pro")
    )
