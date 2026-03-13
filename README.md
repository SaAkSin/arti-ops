# arti-ops v2.0 (ADK 기반 AgentOps 플랫폼)

`arti-ops`는 사내 BookStack(위키)에 정의된 20개 이상의 다중 프로젝트 가이드라인과 전사(Global) 보안 정책을 개발자의 로컬 환경(`.agents/` 등)에 충돌 없이 동기화해 주는 **지능형 CLI / TUI 클라이언트**입니다.

## 🚀 주요 기능

### 1. Docs-as-Agent (위키 연동)
BookStack 에 자연어로 작성해둔 룰셋을 API로 가져와 개발 환경 구성 코드로 변환/적용합니다.
(현재 L1 Global 규칙과 L2 Workspace 규칙의 혼합 지원)

### 2. Multi-Agent 파이프라인 (Google ADK 기반)
*   **ContextProfiler:** 호스트 상태와 원격 정책 스캔.
*   **SkillArchitect:** 계층형(Mix-in) 파이썬 배포 스크립트 작성.
*   **CriticalVerifier:** 핵심 보안 위반 및 파괴적 코드 변경 감사 (Red-Team).
*   **DeploymentExecutor:** `ContainerCodeExecutor` 를 통한 샌드박스 안전 격리 검증 및 배포 적용.

### 3. GWS ChatOps (Human-in-the-Loop)
치명적 병합 충돌이나 관리자의 승인이 필요한 파괴적 변경 발생 시 프로세스를 강제 중단(Pause)하고 구글 워크스페이스 챗봇 웹훅으로 승인 카드를 통보합니다. (현재 로직 구성 완료상태)

### 4. 실시간 TUI 뷰어
터미널에서 명령어 입력 시 `Textual` 라이브러리로 구성된 대시보드를 통해 에이전트들의 진행 궤적과 로그를 실시간으로 스트리밍 열람 가능합니다.

---

## 💻 설치 및 동작 방식

본 프로젝트는 의존성 관리 도구인 `uv` 기반으로 설계되었습니다. 파이썬 `3.10` 이상의 버전을 권장합니다.

```bash
# Repo Clone
git clone https://github.com/SaAkSin/arti-ops.git
cd arti-ops

# uv 환경설정 및 설치
uv sync

# CLI 테스트 및 확인
uv run arti-ops --help
```

### 테스트용 실행 명령어

*타겟이 되는 가상의 워크스페이스 프로젝트 아이디를 뒤에 넣습니다.*
```bash
uv run arti-ops sync --workspace Project_Alpha
```

---

## 🛠 기술 스택

*   **Language:** Python 3.10+
*   **Agent Framework:** Google ADK (`Agent`, `Runner`, `WorkflowEngine`)
*   **Dependencies:** `Textual` (TUI), `httpx` (API Client), `pydantic`
*   **Testing/Env:** `uv` (Fast Python Package Installer)

## 📌 라이선스 및 문의
사내 전용 툴셋으로 각 프로젝트 별 PM (BookStack 담당자)에게 L2 권한 문의 바랍니다.
