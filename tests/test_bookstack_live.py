import pytest
import os
from arti_ops.tools.bookstack import BookStackToolset

# 이 테스트는 실제 .env 에 지정된 BookStack 서버를 조회합니다.
# pytest 명령 시 라이브러스트를 건너뛰려면 pytest -m "not live" 로 수행하거나
# .env 토큰이 없으면 skip 되도록 구성합니다.
pytestmark = pytest.mark.skipif(
    not os.getenv("BOOKSTACK_TOKEN_ID"), 
    reason="BookStack 토큰이 설정되지 않아 Live 테스트를 건너뜁니다."
)

@pytest.fixture
def live_bookstack_tool():
    """실제 .env 환경 변수를 사용하는 BookStackToolset 인스턴스"""
    return BookStackToolset()

@pytest.mark.asyncio
async def test_live_fetch_global_policy(live_bookstack_tool):
    """실제 통신을 통한 Global(L1) 정책 조회 테스트"""
    response = await live_bookstack_tool.fetch_policies(scope_tag="global")
    
    # 올바르게 API를 조회했는지, 혹은 없는 문서인지 최소한 문자열로 반환됨을 확인
    print(f"\n[Global L1 룰 응답]:\n{response}\n")
    assert isinstance(response, str)

@pytest.mark.asyncio
async def test_live_fetch_workspace_policy(live_bookstack_tool):
    """실제 통신을 통한 Workspace(L2) 정책 조회 테스트"""
    # 사용자가 준비 중인 임의의 테스트용 workspace id
    project_id = "Project_Alpha"
    response = await live_bookstack_tool.fetch_policies(scope_tag="workspace", project_id=project_id)
    
    print(f"\n[Workspace L2 룰 응답 ({project_id})]:\n{response}\n")
    assert isinstance(response, str)
