# 📄 [PRD] arti-ops v2.0 제품 요구사항 명세서

## 1. 제품 개요 (Product Overview)

* **제품명:** arti-ops (ADK 기반 Antigravity 통합 AgentOps 플랫폼)
* **목적:** 20개 이상의 다중 프로젝트에서 활동하는 AI 에이전트(Antigravity)의 Rule, Skill, Workflow를 **BookStack(사내 위키)에서 중앙 통제**하고, 전역(Global) 정책과 개별 프로젝트(Workspace) 정책을 충돌 없이 안전하게 **자동 병합(Soft-Merge) 및 배포**하는 지능형 CLI/TUI 환경 구축.
* **핵심 가치:**
1. **Docs-as-Agent:** 코드를 몰라도 BookStack에 자연어로 정책을 쓰면 에이전트가 이를 코드로 변환하여 배포합니다.
2. **계층형 거버넌스:** 전사 공통 보안 규칙(Global)은 강제하되, 프로젝트 팀의 자율적인 환경(Workspace) 구축을 지원합니다.
3. **Zero-Friction:** `uv` 패키지 매니저 기반 1분 자동 설치 및 무중단 업데이트를 제공합니다.



## 2. 타겟 사용자 및 유저 스토리 (User Personas)

* **AI 플랫폼/보안 엔지니어 (Admin):**
> "사내 보안 가이드라인이 변경될 때, BookStack의 'Global Rule' 페이지를 수정하기만 하면 20개 프로젝트의 로컬 환경에 일괄 강제 동기화되기를 원한다."


* **프로젝트 PM / 리드 개발자 (Manager):**
> "우리 프로젝트에 특화된 DB 스킬을 BookStack에 작성해두면, 팀원들이 명령어 하나로 환경을 세팅하길 원한다. 또한 파괴적 변경 발생 시 GWS 메신저를 통해 배포를 통제(승인/반려)하고 싶다."


* **일반 개발자 (User):**
> "복잡한 세팅 없이 터미널에서 `arti-ops sync` 명령어 한 줄로 최신 전역/로컬 룰을 내 PC에 안전하게 병합하고 싶다."



## 3. 핵심 기능 요구사항 (Functional Requirements)

### F1. BookStack API 양방향 연동 (SSOT & DocOps)

* **REQ-1.1 [Read - 지식 동기화]:** `arti-ops` 실행 시 사내 BookStack API를 호출하여 최신 마크다운 기반의 Rule과 Skill 가이드라인을 동적으로 Fetch 해야 한다.
* **REQ-1.2 [Write - 자동 문서화]:** 배포가 완료되거나 AI가 로컬 환경에 맞춰 스킬 코드를 리팩토링한 경우, 변경된 소스와 Diff 요약을 해당 프로젝트의 BookStack 'Release Notes' 페이지에 자동으로 업데이트(Sync-back) 해야 한다.

### F2. 전역(Global) vs 워크스페이스(Workspace) 계층형 설정 관리

* **REQ-2.1 [Global Scope]:** 사내 보안 룰, 공통 API 연동 스킬 등 모든 프로젝트에 **최우선으로 강제 적용**되는 정책 (절대 우회 및 덮어쓰기 불가).
* **REQ-2.2 [Workspace Scope]:** 특정 프로젝트 전용 도메인 특화 프롬프트 및 의존성. (Global 정책을 위반하지 않는 선에서 적용됨).
* **REQ-2.3 [스마트 병합]:** 두 계층의 설정이 충돌할 경우, AI 메타 에이전트가 문맥을 분석하여 Global 정책을 절대 위반하지 않는 선에서 Workspace의 특수성을 유지하도록 코드를 자율 병합(Mix-in)한다.

### F3. 다중 에이전트 오케스트레이션 및 샌드박스 검증

* **REQ-3.1 [Agent Crew]:** 컨텍스트 수집(Profiler), 병합 기획(Architect), 정책 검증(Verifier), 배포 실행(Executor)으로 역할을 분리한 4개의 ADK 에이전트가 파이프라인을 구성한다.
* **REQ-3.2 [컨테이너 샌드박싱]:** 생성된 배포 스크립트는 로컬 호스트에 반영되기 전, ADK `ContainerCodeExecutor`를 활용해 타겟 환경과 동일한 컨테이너(Docker/Podman)에서 안전성 검증(Dry-run)을 100% 통과해야 한다.

### F4. HITL (Human-in-the-Loop) 및 GWS ChatOps

* **REQ-4.1 [승인 대기]:** 기존 핵심 룰을 삭제하거나 파괴적 변경 감지, 또는 해결 불가능한 정책 충돌 시 프로세스를 일시 정지(Pause)한다.
* **REQ-4.2 [웹훅 연동]:** GWS Chat으로 Diff 요약과 함께 승인 인터랙티브 카드를 발송하며, PM의 피드백 입력 시 워크플로우를 재개(Resume)한다.
