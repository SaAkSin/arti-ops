# 📄 [PRD] arti-ops v0.5.2 제품 요구사항 명세서 (전면 개정판)

## 1. 제품 개요 (Product Overview)

* **제품명:** arti-ops (로컬 컨텍스트 기반 AgentOps TUI 플랫폼 및 다중 에이전트 스웜 팩토리)
* **목적:** 사용자가 터미널 환경에서 백로그를 관리하고, 사내 위키(BookStack)와 로컬 파일 시스템을 교차 분석하여 맞춤형 스킬/룰을 자동 생성하는 TUI 및 분리된 작업자 에이전트 워크트리 환경의 통합.
* **핵심 가치:** 단일 파이프라인에서 벗어나 `arti-adapter` 워크플로우를 통한 비파괴적 스웜 인프라 주입으로 다중 에이전트(`arti_core`, `arti_cli`, `arti_reviewer`, `arti_pm`)가 자율 코딩하고 검증(Ralph Loop)하는 자율주행 체계의 실현.

## 2. 핵심 기능 요구사항 (Functional Requirements)

* **F1. 위키-로컬 융합 프롬프트 주도 생성 (Workspace Context Fusion):**
  * 시스템은 사내 위키(BookStack)와 로컬 컨텍스트를 스캔하여 타겟 에이전트용 규격(`.agents/skills/`)으로 생성.
* **F2. 자율 정책 검증 및 Ralph Loop 방어망:**
  * 생성된 스킬과 코드는 L1 보안 정책에 의해 검증되고, 각 워크트리는 `ralph-loop.sh`의 3회 이상 실패 감지 시 `7-failed` 로 데드락 방지.
* **F3. 전체화면 대화형 TUI 및 계층적 원격 프리뷰 (Full-screen Console):**
  * 콘솔 전체화면 모드(`prompt_toolkit` 기반)에서 직관적 트리 진행도 및 `list` 뷰어 지원.
  * 기존 `rules`, `skills`에 이어 `.agents/workflows/` 경로도 함께 스캔하여 표시.
  * **[신규]** 로컬 워크스페이스 파일(L2), 로컬 전역 파일(L1), 북스택 워크스페이스 원격 파일(G2), 북스택 글로벌 원격 파일(G1)을 직관적인 뱃지([L2], [L1], [G2], [G1]) 형태의 계층 구조로 리스트에 동시 노출.
  * **[신규]** 오프라인 원격 파일 선택 시, G1 전역 및 G2 워크스페이스 캐시에서 본문을 정규식으로 직접 추출하여 실시간 우측 화면 프리뷰 렌더링 지원.
* **F4. 다중 에이전트 칸반 보드 연동 (.agents/board):**
  * 1-backlog부터 6-done까지의 마크다운 티켓을 상태이전(mv) 기반으로 처리하는 스웜 릴레이 지원.
*   **F5. 로컬-위키 연동 대화형 배포 (BookStack Upsert):**
    *   `u` (upsert) 단축키를 통해 BookStack과 로컬 `.agents`를 시각적으로 비교, 반영.
*   **F6. L1 전역 정책 변환 뷰어:**
    *   `g` 단축키로 활성화된 창을 L1 전역 정책(Globalizer 에이전트)으로 일반화 변환 미리보기.
*   **F7. [신규] 마크다운 기반 동적 정책(Policy) 관리 및 조합 (Docs-as-Code):**
    *   기존 BookStack 원격 서버에서 가져오던 정책 구성을 `.agents/` 내 마크다운으로 통합.
    *   YAML Frontmatter를 통해 문서 속성 정의 (`scope`, `type`, `version`, `purposes`).
    *   에이전트 런타임 시(Policy Loader & Composer) `target_version` 및 `target_purposes`에 맞춰 우선순위 별로 병합 캐싱.
*   **F8. [신규] 원격 GitHub 저장소 연동 및 동기화 (Policy Sync Engine):**
    *   글로벌 설정(`~/.arti-ops/credentials`) 또는 기본값(`https://github.com/SaAkSin/arti-swarm.git`, Public)을 통해 정책 문서들을 런타임에 동기화(GitOps).
    *   **브랜치 스위칭 전략 (Scope Routing)**: 동기화 저장소(`~/.arti-ops/policies`)는 단일 디렉토리로 관리됨. 기본적으로 `main` (G1)을 Checkout 하되, 현재 워크스페이스와 동일한 이름의 브랜치 (G2)가 원격에 존재할 경우 해당 브랜치로 Checkout (Switching)하여 단일 구조 안에서 모든 G1/G2 정책(문서 내 Frontmatter `scope: G1|G2`로 식별)을 포괄적으로 스캔.
    *   **권한 관리 (Authorization)**: `arti-swarm.git`의 Collaborators(협업자)로 등록된 인원만이 G1, G2 정책의 병합 및 관리(Push/Upsert) 권한을 가짐. (GitHub Native 권한 활용)
    *   **빈 저장소 시동 (Cold Start) 지원 로직**: 동기화 대상 원격 저장소가 한 번도 커밋되지 않은 완전히 비어있는 깡통 상태일 경우, TUI List Viewer 진입 시 이를 감지하여 사용자에게 `[i: G1 정책 초기화]` 안내를 노출. 단축키 `i`를 누르면 빈 편집기가 열리며, 작성 후 `Ctrl+S`로 저장 시 `main` 브랜치에 첫 커밋과 함께 Push되어 GitOps 환경이 자동으로 부트스트랩됨.
    *   에이전트 파이프라인 초기화 및 `PolicyComposer` 로드 시점에 `git clone` 및 `git fetch & checkout` 을 자동 수행.
    *   동기화된 정책 원본은 로컬 `.agents/`가 아닌 글로벌 영역(`~/.arti-ops/policies`) 단일 폴더에 위치시켜 모든 프로젝트가 통합 관리되도록 함.
    *   `subprocess` 기반 순정 Git 명령어 처리 및 토큰 마스킹 보안 처리.
