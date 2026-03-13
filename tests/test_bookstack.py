import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from arti_ops.tools.bookstack import BookStackToolset

@pytest.fixture
def bookstack_tool(monkeypatch):
    """BookStackToolset 인스턴스 픽스처"""
    monkeypatch.setenv("BOOKSTACK_API_URL", "https://mock.wiki.com")
    monkeypatch.setenv("BOOKSTACK_TOKEN_ID", "test_id")
    monkeypatch.setenv("BOOKSTACK_TOKEN_SECRET", "test_secret")
    return BookStackToolset()

@pytest.mark.asyncio
@patch("httpx.AsyncClient.get")
async def test_fetch_policies_global(mock_get, bookstack_tool):
    """Global (L1) 정책 조회 테스트"""
    mock_books = MagicMock()
    mock_books.json.return_value = {"data": [{"id": 43}]}
    mock_books.status_code = 200
    
    mock_book_detail = MagicMock()
    mock_book_detail.json.return_value = {
        "contents": [
            {
                "type": "chapter",
                "slug": "rules",
                "pages": [{"id": 1, "name": "Global Rule 1"}]
            },
            {
                "type": "chapter",
                "slug": "skills",
                "pages": [{"id": 2, "name": "Global Skill 1"}]
            }
        ]
    }
    mock_book_detail.status_code = 200
    
    mock_page_1 = MagicMock()
    mock_page_1.json.return_value = {"markdown": "Global Rules (L1)\n1. Never use root access."}
    mock_page_1.status_code = 200
    
    mock_page_2 = MagicMock()
    mock_page_2.json.return_value = {"markdown": "Global Skills (L1)\n1. Know Linux."}
    mock_page_2.status_code = 200
    
    mock_get.side_effect = [mock_books, mock_book_detail, mock_page_1, mock_page_2]

    response = await bookstack_tool.fetch_policies(scope_tag="global")
    assert "Global Rules (L1)" in response
    assert "Global Skills (L1)" in response

@pytest.mark.asyncio
@patch("httpx.AsyncClient.get")
async def test_fetch_policies_workspace_success(mock_get, bookstack_tool):
    """Workspace (L2) 정상 조회 테스트"""
    project_id = "Project_Alpha"
    
    mock_books = MagicMock()
    mock_books.json.return_value = {"data": [{"id": 44}]}
    mock_books.status_code = 200
    
    mock_book_detail = MagicMock()
    mock_book_detail.json.return_value = {
        "contents": [
            {
                "type": "chapter",
                "slug": "rules",
                "pages": [{"id": 3, "name": "Workspace Rule 1"}]
            },
            {
                "type": "chapter",
                "slug": "skills",
                "pages": [{"id": 4, "name": "Workspace Skill 1"}]
            }
        ]
    }
    mock_book_detail.status_code = 200
    
    mock_page_3 = MagicMock()
    mock_page_3.json.return_value = {"markdown": f"Workspace {project_id} Rules\n1. Use PostgreSQL"}
    mock_page_3.status_code = 200
    
    mock_page_4 = MagicMock()
    mock_page_4.json.return_value = {"markdown": f"Workspace {project_id} Skills\n1. Python Async"}
    mock_page_4.status_code = 200
    
    mock_get.side_effect = [mock_books, mock_book_detail, mock_page_3, mock_page_4]

    response = await bookstack_tool.fetch_policies(scope_tag="workspace", project_id=project_id)
    assert f"Workspace {project_id} Rules" in response
    assert "PostgreSQL" in response
    assert "Python Async" in response

@pytest.mark.asyncio
async def test_fetch_policies_workspace_missing_id(bookstack_tool):
    """Workspace (L2) 조회 시 project_id가 누락되었을 때의 예외 처리 테스트"""
    response = await bookstack_tool.fetch_policies(scope_tag="workspace")
    assert "Error: Workspace scope requires a project_id." in response

@pytest.mark.asyncio
@patch("httpx.AsyncClient.get")
@patch("httpx.AsyncClient.put")
async def test_publish_sync_report(mock_put, mock_get, bookstack_tool):
    """Sync 결과(Release Notes) 퍼블리싱 테스트"""
    project_id = "Project_Alpha"
    diff_md = "## Changes\n- Installed something"
    
    mock_search = MagicMock()
    mock_search.json.return_value = {"data": [{"id": 3}]}
    mock_search.status_code = 200
    mock_get.return_value = mock_search
    
    mock_put_res = MagicMock()
    mock_put_res.status_code = 200
    mock_put.return_value = mock_put_res

    response = await bookstack_tool.publish_sync_report(project_id=project_id, diff_md=diff_md)
    assert f"Successfully updated Release Notes for project {project_id}" in response
