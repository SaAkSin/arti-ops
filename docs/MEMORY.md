# Arti-Ops 스웜 메모리 및 학습 저장소

이 파일은 `arti-auto` 스웜이 동일한 실수를 반복하지 않고, 아키텍처 의사결정을 지속적으로 보존하기 위해 스스로 관리하는 장기 기억소입니다. AI 에이전트는 작업 시작 전 반드시 이 문서를 정독합니다.

## [🩹 Troubleshooting (오답 노트)]

### 1. 파이썬 클로저 변수 참조 할당 지연 에러 (Variable Hoisting)
* **에러 증상**: 하위 Closure 함수 내부에서 외부 스코프 변수를 참조할 시, 인접 선언부가 하단에 있으면 `NameError: free variable referenced before assignment in enclosing scope` 런타임 오류 발생.
* **DO**: 하위 내부 함수를 선언(def)하고 즉시 호출해야 할 경우, 내부 함수 안에서 캡처(Capture)해 사용할 외부 변수들은 **반드시 내부 함수 선언부 이전 최상단에 물리적으로 초기화**해 두어야 합니다.

### 2. 프로젝트 Root 기반 CLI 구동 시 워크트리 스코프 미반영 이슈 (UI 승인 게이트)
* **상황**: 에이전트가 격리된 워크트리(`.agents/worktrees/arti_core`)에서 TUI 코드(`list_viewer.py`)를 개발 완료하고 사용자에게 시각적 확인(HITL)을 요청함.
* **에러 증상**: 사용자는 루트 폴더에서 `uv run arti-ops`를 입력하여 확인을 시도하므로, 아직 병합되지 않은 워크트리의 UI 코드가 아닌 예전 `main` 브랜치의 UI가 노출됨. (수정사항 노출 안 됨)
* **DO**: **시각적 UI 확인이 필요한 CLI 커맨드 수정 사항**은 사용자가 쉽게 테스트할 수 있도록, 지시를 내리기 직전 가장 먼저 현재 코드를 `main`에 **역병합 (Merge-back)** 및 **sync-worktrees** 시킨 후에 확인을 요청하십시오.
### 3. CLI 외부 도구 버전업 및 Sub-shell PATH 의존성 에러 (Graphify)
* **상황**: 백그라운드 쉘 스크립트(`.agents/scripts/sync-worktrees.sh`) 내부에서 Graphify 추출 명령을 수행함.
* **에러 증상**: `error: unknown command '--update'` (버전업에 의한 CLI 명령어 문법 변경 에러) 및 `graphify: command not found` (서브 쉘의 PATH 환경 변수에 바이너리 경로가 누락됨).
* **DO**: 외부 CLI 툴의 명령 체계가 개편될 경우 (예: `--update` 단일 플래그에서 `update ./` 명령어로), 스크립트 내 하드코딩된 호출부도 **동일하게 최신 사양으로 수정**하십시오.
* **DO**: 외부 툴을 사용하는 스크립트 작성 시, 사용자 개인 로컬의 PATH가 온전히 상속되지 않을 상황에 대비하여, 필수 바이너리 부재로 인한 전체 프로세스 중단을 막기 위해 에러 무시 패턴(`|| true`)과 같은 안전망을 구축하십시오.
## [📐 Architecture & Conventions]
(기존 패턴 학습 시 추가)
