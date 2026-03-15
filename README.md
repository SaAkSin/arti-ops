# arti-ops v0.5.1 (AI AgentOps TUI 플랫폼)

`arti-ops`는 사내 BookStack(위키)에 정의된 20개 이상의 다중 프로젝트 가이드라인과 전사(Global) 보안 정책을 개발자의 로컬 환경과 **자동으로 융합(Soft-Merge)** 및 배포하는 **지능형 전체화면 TUI 클라이언트**입니다.
> **⚠️ 주의:** 이 플랫폼은 아트그래머(ARTGRAMMER) 내부 개발실의 **프로토타입(Prototype) 프로젝트**이며, Google DeepMind의 **`antigravity` 에이전트 전용**으로 설계되었습니다. 다른 에이전트 모델 또는 일반 챗봇 시스템에서는 정상적인 정책 동기화 및 파이프라인 수행을 보장하지 않습니다.

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

## 💻 1초 전역 자동 설치 (권장)

`arti-ops`는 파이썬 환경이나 패키지 매니저(`uv`)의 존재 유무와 관계없이, 터미널에서 다음 명령어 한 줄이면 모든 종속성 설치 및 시스템 전역(Global) 셋업이 완료됩니다.

```bash
curl -fsSL https://arti-ops.artgrammer.co.kr | bash
```
> 설치가 끝나면 터미널에서 `arti-ops init`을 실행하여 워크스페이스를 초기화하세요. 상세한 커스텀 배포 및 수동 설치 방법은 [배포 가이드(docs/deploy_guide.md)](docs/deploy_guide.md)를 참조하세요.

### 테스트용 실행 (소스 코드 클론 시)

저장소를 직접 클론하여 로컬에서 개발/테스트하는 경우:
```bash
uv sync
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
