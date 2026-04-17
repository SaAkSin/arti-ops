---
Status: 1-backlog
Assignee: @arti_cli
DependsOn: None
---

# 002-add-workflows-to-list-viewer-arti_cli

- **목표:** `src/arti_ops/cli/list_viewer.py` 좌측 패널(items) 렌더링 로직에 `workflows` 디렉토리 스캔을 추가.
- **상세 지침:**
  1. `run_list_viewer()` 함수 내부의 `rules`, `skills` 스캔 로직을 참고하여, `workflows` 디렉토리(`.agents/workflows/` 또는 `global_workflows/` 등 워크스페이스 기준 올바른 경로)를 스캔하도록 구현합니다.
  2. 조회된 `.md` 파일들을 좌측 패널 배열(`items`)에 `★ Workflows:` 섹션과 함께 병합합니다.
  3. 다른 `rules`나 `skills`의 L1 변환(`g`), Upsert(`u`) 동작에 문제가 생기지 않는지 검증(`ralph-loop.sh`)을 거치십시오.
