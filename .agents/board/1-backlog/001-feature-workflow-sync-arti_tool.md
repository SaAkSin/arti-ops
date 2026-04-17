# 001-feature-workflow-sync

- **담당:** `@arti_tool`
- **목표:** BookStack 위키 정책 워크플로우(.agents/workflows/) 가져오기 연동 로직 구현
- **실행 지침:**
  1. `.agents/worktrees/arti_tool/` 디렉토리로 이동하세요.
  2. `src/arti_ops/tools/bookstack.py` 모듈 내에 `BookStackToolset`을 확장하여, 위키의 워크플로우 페이지를 API로 읽어와 로컬 `.agents/workflows/` 디렉토리에 .md 포맷으로 동기화(가져오기)하는 도구(`fetch_workflows` 등)를 신규 개발하세요.
  3. 사전에 `docs/PRD.md`와 `docs/SSD.md`에 추가된 신규 워크플로우 요구사항들을 숙지하세요.
  4. 개발 후 단위 테스트를 검증하고, `../../scripts/ralph-loop.sh arti_tool 001-feature-workflow-sync-arti_tool.md` 방어망을 통과한 후 성공을 보고하세요.
