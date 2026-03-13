import os
import pytest
from unittest.mock import patch, MagicMock
from arti_ops.tools.gws_chat import GwsChatTool

@pytest.mark.asyncio
async def test_gws_chat_tool_no_space_id():
    """
    GWS_SPACE_ID가 환경변수에 없을 때 예외가 발생하지 않고 early return 하는지 확인합니다.
    """
    with patch.dict(os.environ, {"GWS_SPACE_ID": ""}):
        tool = GwsChatTool()
        
        with patch("asyncio.create_subprocess_exec") as mock_exec:
            await tool.request_approval("TEST-PROJ", "diff_content", "test_reason")
            # gws_space_id가 없으므로 subprocess가 호출되지 않아야 함
            mock_exec.assert_not_called()

@pytest.mark.asyncio
@patch("arti_ops.tools.gws_chat.asyncio.create_subprocess_exec")
async def test_gws_chat_tool_subprocess_call(mock_create_subprocess_exec):
    """
    GWS CLI subprocess가 주어진 인자대로 올바르게 호출되는지 확인하는 모킹 테스트입니다.
    """
    # 서브프로세스 Mock 설정 (성공 응답 시뮬레이션)
    mock_process = MagicMock()
    # 파이썬 3.8 이상에서는 communicate가 코루틴이므로 AsyncMock 처럼 동작하게 하려면 AsyncMock 사용 필요
    from unittest.mock import AsyncMock
    mock_process.communicate = AsyncMock(return_value=(b"success", b""))
    mock_process.returncode = 0
    mock_create_subprocess_exec.return_value = mock_process
    
    with patch.dict(os.environ, {"GWS_SPACE_ID": "spaces/TEST_SPACE"}):
        tool = GwsChatTool()
    
        await tool.request_approval("TEST-PROJ-01", "```diff\n+ new_line\n```", "의도적인 정책 위반")
    
        # asyncio.create_subprocess_exec 가 올바른 인자들로 호출되었는지 확인
        mock_create_subprocess_exec.assert_called_once()
        args, kwargs = mock_create_subprocess_exec.call_args
        
        assert args[0] == "gws"
        assert args[1] == "chat"
        assert args[2] == "+send"
        assert "--space" in args
        assert "spaces/TEST_SPACE" in args
        assert "--text" in args
        
        # run() 메서드 연계 테스트
        mock_create_subprocess_exec.reset_mock()
        await tool.run("TEST-PROJ-02", "some_diff", "reason")
        mock_create_subprocess_exec.assert_called_once()
