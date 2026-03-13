# 🛠️ [SSD] arti-ops v0.1.0 시스템 및 서비스 명세서

## 1. 시스템 아키텍처 개요 (System Architecture)

Pure Google ADK(Python)의 내장 객체들을 적극 활용하여 시스템을 구성합니다.

```text
[ Client Layer (Local PC) ]
  ├── 🖥️ Textual TUI (`arti-ops`) : Claude CLI 스타일의 마크다운 채팅(ChatBubble) 뷰어
  └── 📂 Target Workspace : 최종 산출물이 병합될 `.agents/` 디렉토리

[ ADK Core Layer (Python) ]
  ├── ⚙️ Runner & SessionService (Database) : 상태 및 배포 이력 영구 저장
  ├── 🕵️ ContextProfiler (Flash) : BookStack 및 로컬 디렉토리 환경 딥 스캔
  ├── 🧠 SkillArchitect (Pro) : 계층 정책 병합 및 배포 스크립트 작성
  ├── 🧐 CriticalVerifier (Pro) : 글로벌 정책 위반 검사 (Self-Correction Loop)
  └── 🚀 DeploymentExecutor (Flash) : 샌드박스 테스트 및 최종 파일 I/O

[ Integration Layer (ADK Tools) ]
  ├── 📚 BookStackToolset (RestApiTool) : BookStack API 통신 (Read/Write)
  ├── 💬 GwsChatTool (LongRunningFunctionTool) : HITL 승인 위한 gws CLI 구동 및 대기
  └── 🐳 SandboxTool (ContainerCodeExecutor) : Docker 기반 안전 격리 실행 환경 (의존성 부족 시 Lazy Load 스킵 처리)

```

## 2. BookStack 데이터 매핑 및 정책 계층 모델 (Hierarchy Model)

BookStack의 논리적 구조를 에이전트의 컨텍스트(스코프)로 1:1 매핑합니다.

| 계층 (우선순위) | BookStack (SSOT) 위치 | 매핑 스코프 (Scope) | 병합 및 반영 원칙 |
| --- | --- | --- | --- |
| **L1 (최상위)** | Book: `Antigravity Global` | **Global Scope** | 회사의 절대적인 보안 규칙. 어떠한 경우에도 로컬 설정이 이를 무시할 수 없음 (수정 불가). |
| **L2** | Book: `Workspace / Proj_A` | **Workspace Scope** | 프로젝트 PM이 위키에 문서화해 둔 도메인 특화 룰. L1과 충돌 시 L1의 가이드에 맞춰 AI가 자동 리팩토링함. |
| **L3** | Local PC (`package.json` 등) | **Local Context** | `ContextProfiler`가 스캔한 현재 로컬 코드베이스의 기술 스택 및 의존성 현황. |
| **L4 (최하위)** | Local PC (`.agents/`) | **Local Artifacts** | 개발자 PC에 남아있는 구형 룰. (상위 계층과 병합 후 덮어쓰기 됨) |

## 3. ADK Tool 연동 명세 (Integration Specs)

### 3.1. BookStackToolset (지식 동기화 모듈)

ADK의 `RestApiTool` 또는 `FunctionTool`을 활용하여 BookStack API를 에이전트 도구로 변환합니다. OS Keyring에 안전하게 저장된 Token을 사용합니다.

* **`fetch_policies(scope_tag: str, project_id: str)`**
* Global 호출 시 Global Book의 마크다운을 Fetch 하여 `Session.state['app:global_rules']`에 적재 (ReadOnly).
* Workspace 호출 시 해당 프로젝트 Book의 마크다운을 Fetch 하여 `Session.state['temp:workspace_rules']`에 적재.


* **`publish_sync_report(project_id: str, diff_md: str)`**
* 배포 성공 후, 병합된 최종 결과물과 Diff 내역을 해당 프로젝트의 BookStack 'Release Notes' 페이지에 `PUT` 요청으로 덮어씀 (문서 현행화).



### 3.2. GWS ChatTool (HITL 제어 모듈)

* ADK의 **`LongRunningFunctionTool`**을 사용하여 비동기 대기를 구현합니다.
* `Verifier`가 치명적 충돌을 감지하면 이 툴을 호출하며, 호출 즉시 ADK 워크플로우는 블로킹 없이 **일시 정지(Pause)**됩니다. PM이 승인하면 API 서버가 `FunctionResponse`를 주입하여 **재개(Resume)**합니다.

## 4. 시스템 동작 시퀀스 다이어그램 (PlantUML)

사용자가 `arti-ops sync --workspace Project_A` 명령어를 실행했을 때, BookStack에서 계층형 정책을 가져와 병합하고, 충돌을 검증(HITL)한 뒤 샌드박스를 거쳐 배포 및 역문서화하는 전체 엔드투엔드(E2E) 시퀀스입니다.

*(아래 코드를 복사하여 마크다운 뷰어나 [PlantUML Web](https://plantuml.com/ko/)에 붙여넣으시면 다이어그램 이미지를 확인하실 수 있습니다.)*

```plantuml
@startuml
!theme plain
skinparam defaultTextAlignment center
skinparam maxMessageSize 150
skinparam ParticipantPadding 10

actor "개발자/PM" as User #F9FAFB
participant "Textual TUI\n(arti-ops CLI)" as CLI #E8F4F8
database "📚 BookStack API\n(SSOT)" as Wiki #FDEBD0

box "Pure ADK Core (Python)" #F8FAFC
participant "Runner & State\n(ADK Core)" as ADK
participant "🕵️ Context Profiler\n(Flash)" as Profiler
participant "🧠 Skill Architect\n(Pro)" as Architect
participant "🧐 Critical Verifier\n(Pro)" as Verifier
participant "🚀 Deploy Executor\n(Flash)" as Executor
end box

boundary "💬 GWS Chat\n(HITL)" as GWS #EBF5FB
participant "🐳 Container\nSandbox" as Sandbox #FDEDEC

== 1. 컨텍스트 수집 및 지식 동기화 (Read) ==
User -> CLI : `arti-ops sync --workspace Proj_A` 실행
CLI -> ADK : run_async() 워크플로우 시작
activate ADK

ADK -> Profiler : 환경 및 정책 수집 지시
activate Profiler
Profiler -> Wiki : [RestApiTool] GET /api/pages (Global 룰)
Wiki --> Profiler : 전사 공통 마크다운 반환 (L1)
Profiler -> Wiki : [RestApiTool] GET /api/pages (Proj_A 룰)
Wiki --> Profiler : 프로젝트 특화 마크다운 반환 (L2)
Profiler -> CLI : 로컬 코드베이스 & 의존성 딥스캔 (L3)
Profiler -> ADK : 수집된 정보를 `Session.state`에 분리 저장\n(global_rules, workspace_rules, local_context)
deactivate Profiler

== 2. 계층형 병합 및 자율 검증 (Self-Correction Loop) ==
loop 최대 3회 반복 (ADK LoopAgent)
    ADK -> Architect : 계층형 정책 병합 기획
    activate Architect
    Architect -> Architect : LLM 추론: 전역 룰(L1)을 절대 준수하며\n프로젝트 특화 스킬(L2)을 안전하게 병합(Mix-in)
    Architect -> ADK : 배포용 스크립트 및 통합 설정\nArtifact 생성 (메모리 임시 저장)
    deactivate Architect
    
    ADK -> Verifier : 산출물 보안/충돌 검증 (Red Team)
    activate Verifier
    Verifier -> Verifier : 글로벌 정책 위반, 의존성 충돌,\n파괴적 스크립트 심사
    
    alt 검증 통과 (PASS)
        Verifier -> ADK : `escalate=True` (루프 탈출 성공)
    else 경미한 오류 / 로직 충돌 (REJECT)
        Verifier -> ADK : State에 반려 사유 기록 (Architect 재기획 지시)
    else 치명적 정책 충돌 (HITL Trigger)
        Verifier -> ADK : [LongRunningTool] GwsChatTool 호출
        ADK -> GWS : [gws CLI] 충돌 내용(Diff) 및 승인/수정 요청 발송
        note right of ADK : 워크플로우 일시 정지 (Yield/Pause)
        GWS -> User : 알림 수신 및 내용 검토
        User -> GWS : "로컬 룰을 무시하고 글로벌 룰 강제 적용해" (피드백)
        GWS --> ADK : `FunctionResponse` 콜백 주입
        ADK -> ADK : 워크플로우 재개 (Resume)
        ADK -> Architect : 사용자 지침을 반영하여 재기획 수행
    end
    deactivate Verifier
end

== 3. 샌드박스 안전 검증 및 최종 배포 (Write) ==
ADK -> Executor : 검증 완료된 Artifact 배포 지시
activate Executor
Executor -> Sandbox : [ContainerCodeExecutor]\n격리된 Docker 샌드박스 구동
activate Sandbox
Sandbox -> Sandbox : 가상 환경에서 배포 스크립트 Dry-run 시뮬레이션
Sandbox --> Executor : 테스트 성공 로그 (Exit 0) 반환
deactivate Sandbox

Executor -> CLI : 실제 File I/O 동기화 (로컬 `.agents/` 덮어쓰기)
CLI --> Executor : 저장 완료
Executor -> Wiki : [RestApiTool] PUT /api/pages\n배포된 최신 룰과 Diff를 BookStack에 Release Note로 기록 (Sync-back)
Wiki --> Executor : 문서 업데이트 완료
Executor -> ADK : 최종 배포 성공 리포트 반환
deactivate Executor

ADK --> CLI : 최종 Event 스트림 종료
deactivate ADK
CLI --> User : ✅ TUI 화면에 최종 적용 결과 및 BookStack 링크 출력

@enduml

```