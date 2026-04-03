# 000-verify-legacy-setup

- **담당:** `@arti_pm` (총괄 PM)
- **목표:** 기존 레거시 코드베이스 의존성 설치 및 워크트리 환경 점검
- **실행 지침:**
  "당신(`arti_pm`)은 이 티켓을 인지하는 즉시 다음을 자율 실행하십시오.
  1. 터미널에서 `bash setup-swarm-adapter.sh` 를 실행하여 워크트리 인프라를 구축하세요.
  2. 스웜 전용 도커 실행: `docker-compose -f .agents/docker-compose.swarm.yml up -d`
  3. 🚨 프레임워크 초기화(`uv init` 등)를 올 절대 하지 마십시오. 대신 기존 프로젝트의 의존성(예: `uv sync` 또는 `pip install -e .`)을 터미널에서 설치하여 구동 무결성을 검증하세요. (로컬 파이썬>=3.10 환경 기반)
  4. `bash .agents/scripts/sync-worktrees.sh` 를 실행하여 기존 코드를 워크트리에 일괄 병합하세요.
  5. 성공 시 이 티켓을 `6-done`으로 이동시키고 완료를 보고하세요."
