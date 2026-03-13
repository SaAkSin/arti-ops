import pytest
from arti_ops.tools.bookstack import BookStackToolset

@pytest.fixture
def bookstack_tool(monkeypatch):
    """BookStackToolset 인스턴스 픽스처"""
    monkeypatch.setenv("BOOKSTACK_API_URL", "https://mock.wiki.com")
    monkeypatch.setenv("BOOKSTACK_TOKEN_ID", "test_id")
    monkeypatch.setenv("BOOKSTACK_TOKEN_SECRET", "test_secret")
    return BookStackToolset()

@pytest.mark.asyncio
async def test_fetch_policies_global(bookstack_tool):
    """Global (L1) 정책 조회 테스트"""
    response = await bookstack_tool.fetch_policies(scope_tag="global")
    assert "Global Rules (L1)" in response
    assert "access" in response

@pytest.mark.asyncio
async def test_fetch_policies_workspace_success(bookstack_tool):
    """Workspace (L2) 정상 조회 테스트"""
    project_id = "Project_Alpha"
    response = await bookstack_tool.fetch_policies(scope_tag="workspace", project_id=project_id)
    assert f"Workspace {project_id} Rules" in response
    assert "PostgreSQL" in response

@pytest.mark.asyncio
async def test_fetch_policies_workspace_missing_id(bookstack_tool):
    """Workspace (L2) 조회 시 project_id가 누락되었을 때의 예외 처리 테스트"""
    response = await bookstack_tool.fetch_policies(scope_tag="workspace")
    assert "Error: Workspace scope requires a project_id." in response

@pytest.mark.asyncio
async def test_publish_sync_report(bookstack_tool):
    """Sync 결과(Release Notes) 퍼블리싱 테스트"""
    project_id = "Project_Alpha"
    diff_md = "## Changes\n- Installed something"
    response = await bookstack_tool.publish_sync_report(project_id=project_id, diff_md=diff_md)
    assert f"Successfully updated Release Notes for project {project_id}" in response
