# 🚀 arti-ops 배포 및 설치 가이드 (deploy_guide.md)

이 문서는 `arti-ops v0.5.1` 클라이언트(TUI 및 에이전트 파이프라인)를 처음 사용하거나 새로운 환경(서버/PC)에 배포하려는 작업자를 위한 **빠르고 쉬운 가이드**입니다.
> **⚠️ 주의:** 이 툴킷은 **아트그래머(ARTGRAMMER) 내부 프로토타입 전용**이며, **`antigravity` 에이전트 전용** 파이프라인을 구동하기 위해 특화되어 있습니다. 타 에이전트 시스템에서는 사용을 권장하지 않습니다.

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

### 옵션 1: 1줄 자동 설치 스크립트 (권장)
사용 중인 PC에 파이썬 관리 도구인 `uv` 가 깔려있는지 여부를 확인하고, 없으면 자동으로 다운로드 한 뒤 `arti-ops` 까지 한 번에 전역(Global) 설치를 진행해 주는 원격 스크립트입니다.
터미널에서 아래 명령어 한 줄만 실행하세요. (이 명령어는 항상 최신 `main` 릴리즈를 추적하여 동기화합니다.)
```bash
curl -fsSL http://arti-ops.artgrammer.co.kr | bash
```

### 옵션 2: 수동 설치 (`uv`가 이미 있는 경우)
만약 본인의 PC에 이미 `uv` 가 설치되어 있다면 터미널에서 아래 명령어를 실행하여 툴을 전역으로 바로 설치합니다.
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

---

## 5. 고급 설정: 커스텀 도메인 설치 주소 생성

가장 짧고 깔끔한 명령어(`curl -sL http://arti-ops.artgrammer.co.kr | bash`) 형태의 사내 배포 포인트를 만들고 싶다면, AWS Route 53과 Github Pages를 조합하여 운영 비용 없이 구축할 수 있습니다.

**요구 사항:**
- 저장소가 Public (공개) 상태이거나 Github Enterprise를 사용 중일 것
- Route 53 호스팅 영역에 대한 관리자 권한

### 1단계: Github Pages 활성화
1. Github 레포지토리의 **Settings > Pages** 메뉴로 이동합니다.
2. **Build and deployment** 섹션의 Source를 `Deploy from a branch`로 설정하고, Branch를 `main`으로 선택 후 Save를 누릅니다.
3. 스크롤을 내려 **Custom domain** 섹션에 연결할 서브도메인을 입력합니다 (예: `arti-ops.artgrammer.co.kr`). Save를 누르면 DNS 검증 대기 상태가 됩니다.

### 2단계: AWS Route 53 설정 (CNAME 레코드 추가)
1. AWS Console에 로그인 후 **Route 53 > 호스팅 영역(Hosted zones)** 으로 이동하여 대상 도메인(`artgrammer.co.kr`)을 클릭합니다.
2. **레코드 생성(Create record)** 버튼을 클릭합니다.
3. 아래 정보를 기입합니다:
   - **레코드 이름(Record name):** 서브도메인 이름 (예: `arti-ops`)
   - **레코드 유형(Record type):** `CNAME`
   - **값(Value):** `<Github-ID>.github.io` (예: `SaAkSin.github.io`)
   - **TTL:** (기본값 300초 유지)
4. **생성**을 눌러 레코드를 저장합니다.

### 3단계: HTTPs 보안 및 루트 라우팅 대기
1. AWS DNS 전파가 끝날 때까지 1~5분 정도 대기합니다.
2. 다시 Github Settings > Pages 로 돌아와서, 입력했던 Custom domain 상태 창이 `DNS check successful` (초록색 체크)로 변했는지 확인합니다.
3. 하단의 **Enforce HTTPS** 옵션을 반드시 **체크**합니다.
4. 이제 브라우저에서 `http://arti-ops.artgrammer.co.kr/install.sh` 에 접속하면 Github의 Raw 스크립트 소스코드 텍스트가 정상적으로 노출되는 것을 볼 수 있습니다.
