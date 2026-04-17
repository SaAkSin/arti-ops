---
Status: 1-backlog
Assignee: @arti_core
DependsOn: 000
---

# 001-review-pipeline-architecture-arti_core

- **목표:** 현재 `src/arti_ops/core/pipeline.py` 기반 시스템 파이프라인 구조 파악 및 스웜 확장을 위한 1차 리뷰 진행
- **실행 지침:**
  "당신(`arti_core`)은 이 티켓 인지 시 다음을 실행하십시오.
  1. 먼저 `DependsOn: 000` 티켓이 `6-done`으로 이동할 때까지 대기하세요.
  2. `setup-swarm-adapter.sh`가 구축해 둔 `.agents/worktrees/arti_core/` 디렉토리 내부에서 작업하십시오.
  3. 터미널 도구로 `graphify query` 혹은 `graphify explain`을 사용해 `pipeline.py`와 `config.py`의 레거시 구조를 파악하세요.
  4. 간단한 리뷰 주석이나 개선 로직을 추가한 뒤, `.agents/scripts/ralph-loop.sh 001-review-pipeline-architecture-arti_core.md arti_core` 를 실행해 기존 테스트를 통과하는지 방어망을 검증하세요.
  5. 검증 완료 후 코드가 안전하다면 티켓을 3-review 단계로 넘기세요."
