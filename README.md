# arti-ops v0.5.0 (AI AgentOps TUI 플랫폼)

`arti-ops`는 사내 BookStack(위키)에 정의된 20개 이상의 다중 프로젝트 가이드라인과 전사(Global) 보안 정책을 개발자의 로컬 환경과 **자동으로 융합(Soft-Merge)** 및 배포하는 **지능형 전체화면 TUI 클라이언트**입니다.

## 🚀 주요 기능

### 1. 로컬 컨텍스트 기반 프롬프트 주도 생성
단순히 위키 텍스트를 다운로드 하는 것이 아니라, 명령어가 실행된 **현재 디렉토리(`os.getcwd()`)의 소스코드 및 기존 `.agents/` 내용**을 딥스캔하여 사용자의 자연어 지시에 딱 맞는 최적의 Rule과 Skill 파일을 자동 생성합니다.

### 2. Multi-Agent 파이프라인 (Google ADK 기반)
* **ContextProfiler:** BookStack(L1/L2 정책) 및 로컬 디렉토리 코드베이스 스캔.
* **SkillArchitect:** 수집된 컨텍스트와 지시어를 융합하여 계층형 파이썬/마크다운 스크립트 도출.
* **CriticalVerifier:** 글로벌 정책 위반 감사 및 TUI 화면에 출력할 [최종 반영 보고서] 생성 (Red-Team).
* **DeploymentExecutor:** 샌드박스 검증 및 최종 `.agents/` 디렉토리 I/O 배포. 완료 시 GWS 요약 알림 전송.

### 3. 전체화면 대화형 TUI (Native IME 기반)
터미널에서 명령어 입력 시 `rich`와 `prompt_toolkit` 라이브러리로 구성된 대시보드를 통해 에이전트들의 진행 궤적, 상태 트리를 실시간으로 열람 가능하며, 하단 프롬프트를 통해 한글을 완벽히 지원하며 자유롭게 피드백을 주고 지시할 수 있습니다.
* **위키 선택 배포:** `u` 또는 `upsert` 입력 시 로컬 생성물과 BookStack을 비교하는 체크박스 다이얼로그가 열리며 원하는 파일만 위키에 배포할 수 있습니다.
* **로컬 현황 대화형 뷰어:** `l` 또는 `list` 입력 시, 별도의 좌우 분할 전체화면 TUI 창이 열립니다. 방향키로 `.agents` 하위의 로컬 에셋 목록(위키 비교 뱃지 포함)을 탐색하고, 스페이스바(Space)로 마크다운 내용을 즉각 미리보기 할 수 있습니다.
* **캐시 리셋:** `r` 또는 `reset` 입력 시 즉각적으로 기존 세션 DB 정보를 지우고 백지 상태로 초기화합니다.
* **즉시 종료:** `q` 입력 시 언제든 안전하게 프로세스 강제 종료(Kill-switch).
* **Self-Correction:** 배포 직전 보고서를 확인 후, 추가 지시사항을 입력하면 AI가 스스로 기획을 수정합니다.

---

## 💻 설치 방법

본 프로젝트는 의존성 관리 도구인 `uv` 기반으로 설계되었습니다. 파이썬 `3.10` 이상의 버전을 권장합니다.

```bash
# Repo Clone
git clone https://github.com/SaAkSin/arti-ops.git
cd arti-ops

# uv 환경설정 및 설치
uv sync

# TUI 앱 접속
uv run arti-ops
```

### 테스트용 실행 명령어

*타겟 프로젝트 ID와 에이전트 종류를 수동으로 지정할 수 있습니다.*
```bash
uv run arti-ops "Project_Alpha" "antigravity"
```

## ⚙️ (참고) 개발자용 Rocky Linux 9 구동 가이드

```bash
# 1. 터미널 UI 깨짐 방지 (이모지 및 스피너 정상 출력)
export LANG="en_US.UTF-8" 

# 2. Podman 데몬 활성화 및 Docker 소켓 환경변수 매핑 (Sandbox 호환)
systemctl --user enable --now podman.socket
export DOCKER_HOST="unix://$XDG_RUNTIME_DIR/podman/podman.sock"
```

---

## 🛠 기술 스택

* **Language:** Python 3.10+
* **Agent Framework:** Google ADK (`Agent`, `Runner`, `WorkflowEngine`)
* **Dependencies:** `rich`, `prompt_toolkit` (TUI), `httpx` (API Client), `pydantic`
* **Test/Build:** `uv`, `pytest`
