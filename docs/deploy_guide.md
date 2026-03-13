# 🚀 arti-ops 배포 및 설치 가이드 (deploy_guide.md)

이 문서는 `arti-ops v0.1.0` 클라이언트(TUI 및 에이전트 파이프라인)를 처음 사용하거나 새로운 환경(서버/PC)에 배포하려는 작업자를 위한 **빠르고 쉬운 가이드**입니다.

---

## 1. 사전 요구 사항 (Prerequisites)

* **운영체제:** Linux (Rocky Linux 9 권장), macOS, Windows (WSL2 권장)
* **Python:** `3.10` 버전 이상 필수
* **패키지 매니저:** **`uv`** (초고속 파이썬 패키지 및 환경 관리자)
  * 설치 방법: `curl -LsSf https://astral.sh/uv/install.sh | sh`
* **(선택) Docker:** Sandbox 시뮬레이션 기능(`DeploymentExecutor`)을 사용하려면 호스트에 Docker가 설치되어 있어야 합니다. (상세 내용은 [Docker 설정 가이드](docker_guide.md) 참조)
* **(선택) GWS CLI:** Google Workspace 채팅 알림/승인을 받기 위한 CLI 유틸리티 (상세 내용은 [GWS 설정 가이드](gws_guide.md) 참조)

---

## 2. 1분 자동 설치 (초기 세팅)

`arti-ops`는 `uv`를 통해 의존성과 가상환경 관리를 한 번에 해결합니다. 복잡한 `pip install` 과정 없이 아래 명령어를 순서대로 실행하세요.

### шаг 1: 저장소 클론
```bash
git clone https://github.com/SaAkSin/arti-ops.git
cd arti-ops
```

### шаг 2: 의존성 동기화 및 가상 환경 자동 생성
이 명령어 하나로 `.python-version`과 `pyproject.toml`에 명시된 버전의 Python 다운로드와 패키지 설치가 완료됩니다.
```bash
uv sync

# 만약 샌드박스(Docker) 기능이 필요하다면 아래 명령어로 확장을 추가로 설치하세요.
uv add "google-adk[extensions]" 
```

### шаг 3: 환경 변수 설정
프로젝트 루트 템플릿(`.env.example`)을 복사하여 `.env` 파일을 생성하고 필수 값을 입력합니다.
```bash
cp .env.example .env
nano .env  # 텍스트 편집기로 API 키 및 각종 정책 설정값 입력
```
*핵심 변수:* `GEMINI_API_KEY`, `GWS_SPACE_ID` (기타 DB 경로 등)

---

## 3. 손쉬운 실행 및 에일리어스(Alias) 등록

매번 `uv run arti-ops ...` 를 타이핑하는 번거로움을 줄이려면 터미널 설정 파일(`.bashrc` 또는 `.zshrc`)에 별칭을 등록하여 시스템 전역에서 사용할 수 있습니다.

```bash
# 본인 환경에 맞게 절대 경로 변경 필요
echo "alias arti-ops='cd /절대/경로/arti-ops && uv run arti-ops'" >> ~/.bashrc
source ~/.bashrc
```

이제 터미널 어디서든 아래 명령어만으로 최신 룰 동기화 TUI 앱을 켤 수 있습니다! 🎉

```bash
arti-ops sync --workspace <대상-프로젝트-ID>
# 예: arti-ops sync --workspace DEMO-W-999
```

---

## 4. 업데이트 및 유지 보수

BookStack 룰이 아니라, `arti-ops` 플랫폼 자체의 코어 소스나 ADK 버전이 업데이트되었다면 아래 두 줄로 최신화가 끝납니다.

```bash
cd arti-ops
git pull origin main
uv sync
```
