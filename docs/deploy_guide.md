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

## 2. 1분 자동 설치 전역(Global) 셋업

`arti-ops`는 파이썬 패키지 매니저인 `uv`를 통해 시스템 전역에 격리된 상태로 매우 쉽게 설치할 수 있습니다.
한 번 설치하면 어느 폴더에서나 `arti-ops` 명령어를 바로 사용할 수 있습니다.

### шаг 1: `uv tool`을 이용한 전역 설치
터미널에서 아래 명령어를 실행하여 툴을 전역으로 설치합니다.
```bash
uv tool install git+https://github.com/SaAkSin/arti-ops.git
```
*(추가 확장 기능이 필요한 경우 패키지 설치 시 `[extensions]` 등의 옵션을 부여할 수 있습니다.)*

### шаг 2: `arti-ops init` 환경 초기화
설치가 완료되면, 터미널 아무 경로(또는 첫 프로젝트 디렉토리)에서 아래 명령어를 쳐서 전역 인증 환경을 구성합니다.
```bash
arti-ops init
```
이 명령어는 대화형 마법사를 실행하여 다음 사항들을 처리해 줍니다:
1. 로컬 폴더 생태계 스캐폴딩 (`.agents/rules`, `.agents/skills`)
2. 로컬 프로젝트 식별자 생성 (`.artiops.toml`)
3. **최초 1회 한정**, 글로벌 통합 인증 정보 입력 (Gemini API, BookStack 등)
   - 입력된 인증키들은 `~/.arti-ops/credentials` 파일에 안전하게 저장되며 이후 모든 프로젝트에서 재활용됩니다.

---

## 3. 손쉬운 실행 

모든 셋업이 완료되었습니다! 
이제 터미널 어디서든 작업 중인 경로 내에서 아래 명령어만으로 대화형 AI TUI 앱이나 배포 동기화를 켤 수 있습니다! 🎉

```bash
# 기본 대화형 모드 진입 (현재 폴더명을 Project ID로 인식)
arti-ops

# 명시적으로 워크스페이스 타겟팅
arti-ops --workspace <대상-프로젝트-ID>
# 예: arti-ops --workspace DEMO-W-999

# 다양한 단축 명령어
arti-ops u  # 로컬 에셋을 BookStack으로 배포(Upsert)
arti-ops l  # 로컬 에셋 현황 조회(List Viewer)
```

---

## 4. 업데이트 및 유지 보수

`arti-ops` 플랫폼 자체의 소스나 기능이 업데이트되었다면, 아래 명령어로 전역 설치본을 최신화할 수 있습니다.

```bash
uv tool upgrade arti-ops
```
