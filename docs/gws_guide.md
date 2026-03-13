# 💬 Google Workspace Chat 웹훅 연동 가이드

`arti-ops`는 정책 동기화 검증 과정에서 자동화로 결정할 수 없는 심각한 룰 충돌이나 파괴적 변경 사항을 감지했을 때, Human-in-the-Loop(HITL) 방식을 도입하여 관리자(PM)에게 최종 결정권을 위임합니다. 이 문서는 구글 워크스페이스(GWS) 챗봇 웹훅을 프로젝트에 통합하는 방법을 설명합니다.

## 1. GWS CLI 설치 및 연동
1. 시스템 레벨에서 GWS CLI(`gws`) 도구가 설치되어 있어야 합니다.
2. `gws auth` 등을 통해 인증 토큰이 활성화된 상태여야 합니다. 

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
*   파이썬 내부에서 `subprocess`나 비동기 쉘 코드를 통해 `gws chat send --space "$GWS_SPACE_ID" --message "..."` 명령을 실행하여 GWS 채널에 `Diff` 내용과 충돌 사유(`conflict_reason`)를 발송합니다.

## 4. 백오피스(콜백)를 통한 Resume(재개) 처리 방법
현재 `arti-ops` TUI/CLI 버전에서는 승인/거절 로직이 백엔드 REST API가 아닌 터미널 세션 내부에서 제어되거나, 별도의 API Gateway를 거쳐 콜백 주입(Callback Injection)으로 풀리게 진화될 예정입니다. 

승인(Resume)이 떨어지게 되면, `Runner.run_async` 제너레이터에 재개 시그널 혹은 피드백 컨텍스트(예: "진행해", "이 부분은 제외해")를 실어보내면 `SkillArchitect` 등에서부터 루프가 재진입하게 됩니다.

> ⚠️ 이 문서는 `v2.0`의 초기 설계안을 바탕으로 작성되었으므로, 향후 콜백 수신용 FastAPI 서버 등 확장이 이루어지면 상세 엔드포인트 사양이 추가될 수 있습니다.
