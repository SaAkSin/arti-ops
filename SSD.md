# 🛠️ [SSD] arti-ops v0.5.0 시스템 및 서비스 명세서 (개정판)

## 1. 시스템 아키텍처 개요

```text
[ TUI Layer (Local Console) ]
  └── 🖥️ Native IME 기반 Full-screen App
      ├── 📜 Main Viewer (상단/중앙) : 진행 과정 트리 (캐시 일치 여부 표시 포함), 에이전트 산출물, 최종 파일 반영 보고서 출력 뷰어
      ├── ⌨️ Input Prompt (하단) : 상시 활성화된 사용자 대화 및 지시어 입력창 (r: 초기화, q: 종료 명령 지원)
      └── ⚡ Event Handler : 'q', 'Ctrl+C' 즉시 종료 글로벌 바인딩

[ ADK Core Layer (Python) ]
  ├── ⚙️ Pipeline Engine : 이벤트 기반 비동기 흐름 제어 및 로컬 승인(HITL) 루프 관리
  ├── 🕵️ ContextProfiler : BookStack 정책(Read) + 현재 실행 경로(로컬 파일, .agents 등) 현황 병합 스캔
  ├── 🧠 SkillArchitect : 수집된 컨텍스트와 '사용자 프롬프트 지시'를 융합하여 Rule/Skill 생성 기획
  ├── 🧐 CriticalVerifier : 정책 위반 검증 및 TUI 화면 출력용 [최종 반영 보고서] 작성
  └── 🚀 DeploymentExecutor : 사용자 UI 승인(Y) 후 실제 로컬 File I/O 및 GWS 요약 송신

[ Integration Layer (Tools) ]
  ├── 📚 BookStackToolset : 정책 Fetch 전용
  ├── 📂 FileIOToolset : 로컬 파일 읽기(컨텍스트 수집) 및 쓰기(최종 배포)
  └── 💬 GwsSummaryTool : 배포 완료 후 단방향 요약 알림 전송 (Pause 기능 완전 제거)

```

## 2. 워크플로우 시퀀스 (Interactive Loop)

1. 사용자가 현재 타겟 경로에서 `arti-ops` 명령어 실행 ➔ 터미널 전체화면 TUI 앱 진입.
2. 하단 프롬프트에 지시 입력 (예: `"r"` 입력 시 즉시 세션 DB 파기 및 초기화).
3. **Profiler**가 로컬 파일 컨텍스트와 BookStack 정책을 수집. 단, 직전 대화 혹은 저장된 `sessions.db`의 컨텍스트로 충분하다고 LLM이 판단한 경우, 도구 호출을 생략하고 캐시 히트(Cache Hit) 메시지(`💡 이전 세션(sessions.db) 기억을 불러왔습니다.`)를 시각적으로 노출한다.
4. **Architect**가 지시와 컨텍스트를 바탕으로 `.agents/skills/...` 및 `.agents/rules/...` 규격에 맞춰 내용 기획 및 생성. 실시간 스트림 파싱을 통해 타겟 파일의 경로를 렌더링한다.
5. **Verifier**가 무결성 검증 후, TUI 화면에 **[반영 예정 파일 목록 및 상세 내용 요약 보고서]**를 제출하고 파이프라인 대기 상태 전환.
6. 사용자가 화면의 보고서를 검토 후 하단 프롬프트에 `승인(y)` 입력 시 **Executor** 가동. 이 때 비동기 Lock(`_pause_event.clear()`) 이슈가 없도록 즉각 블락 해제되어야 한다. `수정해줘` 등 자연어 입력 시 **Architect**로 루프 회귀.
7. 파일 I/O 배포 완료 후 GWS 채팅으로 최종 요약본 단방향 전송.

## 3. 시퀀스 다이어그램 (Sequence Diagram)

```plantuml
@startuml
skinparam handwritten true
skinparam BoxPadding 10
skinparam ParticipantPadding 10
skinparam maxMessageSize 150

actor "개발자/PM" as User #F9FAFB
participant "Native IME\n(arti-ops CLI)" as CLI #E8F4F8
database "📚 BookStack API\n(SSOT)" as Wiki #FDEBD0

box "Python ADK Pipeline" #F8FAFC
  participant "Context Profiler\n(Cache Manager)" as Profiler #E0F2F1
  participant "Skill Architect" as Architect #FFF9C4
  participant "Critical Verifier" as Verifier #FFEBEE
  participant "Deployment Executor" as Executor #E8EAF6
end box

== 1. 파이프라인 초기화 및 캐시 히트 (Context Sync) ==
User -> CLI : `uv run arti-ops` 및\n자연어 프롬프트 지시 입력\n(r 누를 시 세션 DB 즉각 파기)
activate CLI
CLI -> Profiler : 환경 및 정책 수집 지시
activate Profiler

alt LLM 판단: "기존 세션만으로 충분함" (Cache Hit)
    Profiler -> CLI : 💡 이전 세션(sessions.db) 기억 로드
else 정밀 스캔 필요
    Profiler -> Wiki : [RestApiTool] 정책 마크다운 반환
    Profiler -> CLI : [FileIOTool] 로컬 디렉토리 및\n파일 내용 독해 (L3)
end

Profiler -> Architect : 수집/로드된 컨텍스트 및\n지시사항 전달
deactivate Profiler

== 2. 에이전트 기획 및 자율 검증 (Planning & Verification) ==
activate Architect
Architect -> Architect : LLM 추론: 전역 룰을 준수하며\n프로젝트 특화 스킬 및 룰 융합 생성
Architect -> CLI : 실시간 스트림 파싱\n(타겟 파일명 UI 렌더링)
Architect -> Verifier : 배포용 산출물 텍스트 전달
deactivate Architect
    
activate Verifier
Verifier -> Verifier : 글로벌 정책 위반, 타당성 검사,\n[최종 반영 보고서] 작성

alt 검증 통과 (SUCCESS)
    Verifier -> CLI : pending_final_approval 이벤트 및\n보고서 산출물 전달
else 경미한 오류 (REJECT)
    Verifier -> Architect : 반려 사유 기록하여 재기획 회귀
end
deactivate Verifier

== 3. 대화형 로컬 승인 (HITL) 및 배포 ==
CLI -> User : 📄 [최종 반영 검토 보고서] 렌더링\n및 승인 대기
User -> CLI : 승인('y') / 수정 지시 / 종료('q')

alt 'y' 승인
    CLI -> Executor : 비동기 제어권 반환 (pause_event.set())
    activate Executor
    Executor -> CLI : [FileIOTool] 실제 로컬 .agents/\n디렉토리에 I/O 배포 수행
    CLI --> Executor : 저장 완료
    Executor -> User : [GwsSummaryTool] 배포 성공 결과 및\n요약본 단방향 GWS 전송
    Executor -> CLI : 최종 스트림 성공 반환
    deactivate Executor
    CLI --> User : 파이프라인 작업 완료 안내
else 수정 지시 (자연어 피드백)
    CLI -> Architect : 유저 피드백 기반\n파이프라인 루프 재가동
end

deactivate CLI

@enduml
```