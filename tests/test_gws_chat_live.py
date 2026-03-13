import os
import pytest
from dotenv import load_dotenv

# dotenv 명시적 로딩
load_dotenv()

from arti_ops.tools.gws_chat import GwsChatTool

@pytest.mark.asyncio
@pytest.mark.skipif(
    not os.getenv("GWS_SPACE_ID"), 
    reason="GWS_SPACE_ID가 없습니다. 실제 발송 테스트는 환경변수가 설정되어야 합니다."
)
async def test_gws_chat_tool_live_send():
    """
    실제로 GWS 채널에 Webhook(CLI) 메시지를 발송해보는 통합/라이브 테스트입니다.
    이 테스트는 로컬 .env 에 GWS_SPACE_ID가 지정되어 있을 때만 수행됩니다.
    """
    tool = GwsChatTool()
    
    project_id = "arti-ops-live-test"
    diff_md = "```diff\n- old_rule_ignored\n+ new_global_rule_enforced\n```"
    conflict_reason = "L1 글로벌 룰과 워크스페이스(L2) 설정 충돌 감지. (이 메시지는 테스트 발송입니다)"
    
    # 예외 없이 함수가 실행되고, 프로세스가 정상 종료되는지 점검
    await tool.request_approval(project_id, diff_md, conflict_reason)
    
    # GwsChatTool의 run은 ADK Pipeline Pause를 위해 dict를 반환해야함.
    result = await tool.run(f"{project_id}-run-method", diff_md, conflict_reason)
    
    assert isinstance(result, dict)
    assert result.get("status") == "pending_approval"
    assert "arti-ops-live-test" in result.get("project_id", "")
