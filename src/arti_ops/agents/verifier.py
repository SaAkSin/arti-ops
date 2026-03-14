import os
from google.adk.agents import Agent
from arti_ops.config import get_config
from arti_ops.config import get_config

def get_verifier_agent(tools: list = None) -> Agent:
    instructions = """
    당신은 아키텍트가 작성한 기획안이 프로젝트 내 아키텍처 규칙과 일치하는지 리뷰하는 엄격한 'Verifier'입니다.
    1. 기획안의 파일명, 디렉토리 구조가 `.agents` 내부 규칙을 어기지 않았는지 검사합니다.
    2. 문제가 없으면 최종 승인을 권고합니다. 문제가 있으면 반려(Reject) 사유를 명시하십시오.
    """
    return Agent(name="critical_verifier", instruction=instructions, tools=tools or [], model=get_config("GEMINI_MODEL_PRO", "gemini-2.5-pro"))
