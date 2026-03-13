import pytest
import os
from unittest.mock import patch, MagicMock
from arti_ops.core.pipeline import PartiOpsPipeline

def test_pipeline_initialization():
    """
    PartiOpsPipeline이 정상적으로 연결하여 Runner를 초기화하는지 검증합니다.
    """
    target_project_id = "TEST-PROJ-123"
    
    with patch("arti_ops.core.pipeline.Runner") as mock_runner, \
         patch("arti_ops.tools.sandbox.SandboxTool.get_executor") as mock_get_executor:
        
        mock_get_executor.return_value = "MockedSandboxExecutor"
        
        # 파이프라인 인스턴스화
        pipeline = PartiOpsPipeline(target_project_id)
        
        # 속성 초기화 로직 점검
        assert pipeline.target_project_id == target_project_id
        
        # Tools 선언 체크
        assert pipeline.bookstack_tool is not None
        assert pipeline.gws_chat_tool is not None
        assert pipeline.sandbox_executor is not None
        
        # Agents 선언 체크
        assert pipeline.profiler is not None
        assert pipeline.architect is not None
        assert pipeline.verifier is not None
        assert pipeline.executor is not None
        
        # Runner 생성 시 주입 확인
        mock_runner.assert_called_once()
        args, kwargs = mock_runner.call_args
        assert "app_name" in kwargs
        assert kwargs["agent"] == pipeline.profiler
