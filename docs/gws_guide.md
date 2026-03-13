# 💬 Google Workspace Chat 웹훅 연동 가이드

`arti-ops`는 정책 동기화 검증 과정에서 자동화로 결정할 수 없는 심각한 룰 충돌이나 파괴적 변경 사항을 감지했을 때, Human-in-the-Loop(HITL) 방식을 도입하여 관리자(PM)에게 최종 결정권을 위임합니다. 이 문서는 구글 워크스페이스(GWS) 챗봇 웹훅을 프로젝트에 통합하는 방법을 설명합니다.

## 1. GWS CLI 설치 및 연동
`arti-ops` 내부에서 직접 gws를 설치하거나 관리하지 않습니다. **사전 준비된 로컬 OS 환경**에서 인증이 완료되어 있어야 워크플로우 통과가 가능합니다.

### 1-A. 설치 방법
* MacOS (Homebrew): `brew install gws`
* Linux (Binary):
  ```bash
  curl -Lo gws https://github.com/kimtree/gws/releases/latest/download/gws_linux_amd64
  chmod +x gws
  sudo mv gws /usr/local/bin/
  ```

### 1-B. 연동 및 인증 (1회성)
GWS CLI 구동을 위해서는 GCP(Google Cloud Platform) 프로젝트 내 OAuth 동의 구성과 데스크톱 앱용 OAuth 클라이언트 ID가 필요합니다.

1. **OAuth 클라이언트 구성 (`gws auth setup`)**
   - 구글 클라우드 콘솔에 로그인할 수 있는 계정으로 터미널에서 `gws auth setup` 명령어를 실행하여 GCP 프로젝트를 할당하고 OAuth 클라이언트를 설정합니다.
   - ⚠️ **주의**: 위 명령은 로컬 호스트에 `gcloud` CLI 툴이 설치되어 있어야 동작합니다. (`gcloud CLI not found` 에러 발생 시 아래 수동 발급 방법을 사용하세요.)

2. **수동 발급 옵션 (gcloud가 없는 경우 추천)**
   - [Google Cloud Console - API 및 서비스 > 사용자 인증 정보](https://console.cloud.google.com/apis/credentials) 페이지에 접속합니다.
   - 본인이 소유한 프로젝트에서 **"사용자 인증 정보 만들기" > "OAuth 클라이언트 ID"**를 선택합니다.
   - 애플리케이션 유형을 **"데스크톱 앱(Desktop app)"**으로 선택하고 생성합니다.
   - 생성된 클라이언트의 JSON 파일을 다운로드 받아 이름을 `client_secret.json`으로 변경한 후, 프로젝트 루트 경로인 `credentials/client_secret.json` 에 배치합니다.
   - ⚠️ `credentials/` 폴더는 `.gitignore` 처리되어 있어 안전합니다.

3. **로그인 인증 (`gws auth login`)**
   - 클라이언트 설정(1 또는 2)이 준비된 후 프로젝트 루트 디렉토리에서 아래 명령어를 실행합니다.
   - `gws --client-secret credentials/client_secret.json --token credentials/token.json auth login`
   - 브라우저에 표시되는 가이드에 따라 Google 계정 접근 권한 부여를 수락합니다.

4. 터미널 인증이 완료되면 정상적으로 gws 명령어를 사용할 준비가 끝납니다.

## 2. 프로젝트 환경변수 설정
메시지를 발송할 대상 Space ID를 `arti-ops` 프로젝트 루트의 `.env` 파일에 다음과 같이 추가합니다.

```env
# .env
GWS_SPACE_ID="spaces/XXXXXXX"
```

## 3. GwsChatTool의 동작 원리
`src/arti_ops/tools/gws_chat.py` 모듈은 Google ADK의 `LongRunningFunctionTool` 인터페이스를 상속받아 호스트 머신의 CLI를 트리거하도록 설계되었습니다.

*   `CriticalVerifier` 에이전트가 "사람의 검토가 필요하다"고 판단하면, `run` 메서드를 호출합니다.
*   에이전트가 해당 툴을 실행하는 즉시 메인 `Runner` 파이프라인의 **이벤트 스트림은 `Pause`(일시 정지) 상태로 전환**됩니다(Async Yield).
*   파이썬 내부에서 `subprocess`나 비동기 쉘 코드를 통해 프로젝트 종속 인증 옵션을 포함한 발송 명령을 실행합니다.
    - 예시: `gws --client-secret credentials/client_secret.json --token credentials/token.json chat send --space "$GWS_SPACE_ID" --message "..."`

## 4. 백오피스(콜백)를 통한 Resume(재개) 처리 방법
현재 `arti-ops` TUI/CLI 버전에서는 승인/거절 로직이 백엔드 REST API가 아닌 터미널 세션 내부에서 제어되거나, 별도의 API Gateway를 거쳐 콜백 주입(Callback Injection)으로 풀리게 진화될 예정입니다. 

승인(Resume)이 떨어지게 되면, `Runner.run_async` 제너레이터에 재개 시그널 혹은 피드백 컨텍스트(예: "진행해", "이 부분은 제외해")를 실어보내면 `SkillArchitect` 등에서부터 루프가 재진입하게 됩니다.

> ⚠️ 이 문서는 `v2.0`의 초기 설계안을 바탕으로 작성되었으므로, 향후 콜백 수신용 FastAPI 서버 등 확장이 이루어지면 상세 엔드포인트 사양이 추가될 수 있습니다.
