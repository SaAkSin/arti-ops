import pytest
from arti_ops.core.pipeline import ArtiOpsPipeline

def test_pipeline_initialization():
    """
    ArtiOpsPipeline이 정상적으로 도구 및 에이전트를 초기화하는지 검증합니다.
    """
    target_project_id = "TEST-PROJ-123"
    pipeline = ArtiOpsPipeline(target_project_id)
        
    # 속성 초기화 로직 점검
    assert pipeline.target_project_id == target_project_id
        
    # Tools 선언 체크
    assert pipeline.bookstack_tool is not None
    assert pipeline.file_io_tool is not None
    assert pipeline.sandbox_tool is not None
    assert pipeline.gws_chat_tool is not None
        
    # Agents 선언 체크
    assert pipeline.profiler is not None
    assert pipeline.architect is not None
    assert pipeline.verifier is not None
    assert pipeline.executor is not None
    
    # Session service 주입 확인
    assert pipeline.session_service is not None
