import os
from google.adk.agents import Agent
from arti_ops.config import get_config
from arti_ops.core.policy_composer import PolicyComposer

def get_verifier_agent(tools: list = None, version: str = "latest") -> Agent:
    composer = PolicyComposer()
    dynamic_policy = composer.compose(target_version=version, target_purposes=["verifier", "all"])

    instructions = f"""
    당신은 아키텍트가 작성한 기획안이 문서 정책과 일치하는지 리뷰하는 엄격한 'Verifier'입니다.
    
    [통합 정책 컨텍스트]
    {dynamic_policy}

    1. 기획안의 파일명, 디렉토리 구조가 룰 파일은 `.agents/rules/[규칙명].md`, 스킬 파일은 `.agents/skills/[스킬명]/SKILL.md` 포맷을 정확히 따르는지 검사합니다.
    2. 에이전트 이름이 경로 디렉토리명에 포함되어 있다면 절대 허용하지 말고 반려 사유를 명시하십시오.
    3. 정책 컨텍스트에 위배되는 내용이 있다면 반려하십시오.
    4. 문제가 없으면 최종 승인을 권고합니다.
    """
    return Agent(name="critical_verifier", instruction=instructions, tools=tools or [], model=get_config("GEMINI_MODEL_PRO", "gemini-2.5-pro"))
