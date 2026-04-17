# 002-feature-workflow-sync-cli

- **담당:** `@arti_cli`
- **목표:** TUI 메뉴 및 프롬프트에서 워크플로우 동기화 옵션 추가 및 List Viewer(`list_viewer.py`) 최신화
- **실행 지침:**
  1. `.agents/worktrees/arti_cli/` 디렉토리 내부에서만 작업을 수행하세요.
  2. `src/arti_ops/cli/main.py` 내의 프롬프트 상태표시줄(bottom bar) 및 대화형 다이얼로그(`u` upsert 명령어) 처리 로직을 수정하여, Workflow 문서 계층 동기화 옵션이 사용자 UI에 제공되도록 구성하세요.
  3. `src/arti_ops/cli/list_viewer.py` 스플릿 뷰어 좌측 트리에 기존 Rules, Skills 외에 새롭게 생성될 `Workflows` 디렉토리 항목도 정상적으로 목록 렌더링되도록 기능을 확장하세요.
  4. 개발 완료 후 `../../scripts/ralph-loop.sh arti_cli 002-feature-workflow-sync-cli-arti_cli.md`를 통과해야 합니다.
