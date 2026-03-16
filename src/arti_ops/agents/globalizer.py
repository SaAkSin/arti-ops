from google.adk.agents import Agent
from arti_ops.config import get_config


def get_globalizer_agent() -> Agent:
    """L3 프로젝트 전용 규칙/스킬을 L1 글로벌 정책으로 일반화하는 에이전트."""
    instruction = """
    당신은 L3 프로젝트 전용 규칙/스킬을 L1 글로벌 정책으로 일반화하는 전문가입니다.
    입력받은 마크다운 파일 내용을 다음 규칙에 따라 변환하세요:

    1. 프로젝트 고유명, 특정 디렉토리 경로, 워크스페이스 전용 언급을 제거하거나 일반적인 표현으로 대체합니다.
    2. YAML frontmatter는 유지하되 name/description은 여러 프로젝트에 적용 가능한 범용적 내용으로 수정합니다.
    3. 여러 프로젝트에 도입 가능한 보편적 원칙과 가이드라인 위주로 작성합니다.
    4. 한국어로 작성합니다.
    5. 변환된 마크다운만 출력합니다. 부가 설명이나 안내 문구는 포함하지 않습니다.
    """
    return Agent(
        name="l1_globalizer",
        instruction=instruction,
        tools=[],
        # L1 변환은 내용 품질이 중요하므로 PRO 모델 사용
        model=get_config("GEMINI_MODEL_PRO", "gemini-2.5-pro")
    )
