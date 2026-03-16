import os
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from arti_ops.tools.gws_chat import GwsChatTool


@pytest.mark.asyncio
async def test_gws_chat_no_space_id():
    """
    GWS_SPACE_ID가 없을 때 send_summary()가 예외 없이 early return 하는지 확인합니다.
    """
    with patch("arti_ops.tools.gws_chat.get_config", return_value=""):
        tool = GwsChatTool()
        with patch("asyncio.create_subprocess_exec") as mock_exec:
            result = await tool.send_summary("TEST-PROJ", "배포 요약 내용")
            # GWS_SPACE_ID가 없으므로 subprocess가 호출되지 않아야 함
            mock_exec.assert_not_called()
            assert "Skipped" in result


@pytest.mark.asyncio
@patch("arti_ops.tools.gws_chat.asyncio.create_subprocess_exec")
async def test_gws_chat_subprocess_call(mock_create_subprocess_exec):
    """
    GWS CLI subprocess가 올바른 인자로 호출되는지 확인하는 모킹 테스트입니다.
    """
    # 서브프로세스 Mock 설정 (성공 응답 시뮬레이션)
    mock_process = MagicMock()
    mock_process.communicate = AsyncMock(return_value=(b"success", b""))
    mock_process.returncode = 0
    mock_create_subprocess_exec.return_value = mock_process

    with patch("arti_ops.tools.gws_chat.get_config", return_value="spaces/TEST_SPACE"):
        tool = GwsChatTool()
        result = await tool.send_summary("TEST-PROJ-01", "```diff\n+ new_line\n```")

    # asyncio.create_subprocess_exec 가 올바른 인자들로 호출되었는지 확인
    mock_create_subprocess_exec.assert_called_once()
    args, kwargs = mock_create_subprocess_exec.call_args

    assert args[0] == "gws"
    assert args[1] == "chat"
    assert args[2] == "+send"
    assert "--space" in args
    assert "spaces/TEST_SPACE" in args
    assert "--text" in args
    assert "TEST-PROJ-01" in result or "successfully" in result
