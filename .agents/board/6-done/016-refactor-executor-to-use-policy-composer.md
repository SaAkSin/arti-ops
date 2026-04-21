---
Assignee: arti_core
Status: backlog
DependsOn: 015
---

# 📝 Ticket 016: 기존 플랫폼 연동 대체 및 시스템 프롬프트 업데이트

## 1. 개요 (Objective)
ADK 에이전트 실행 시, 이전의 무거운 BookStack 기반 프롬프트 로딩 모듈 대신 신규 `PolicyComposer`를 연동하여 완전한 로컬(Docs-as-code) 방식으로 프롬프트를 갱신합니다.

## 2. 세부 요구사항 (Requirements)
* `src/arti_ops/agents/executor.py` 및 파이프라인 엔진(`pipeline.py` 혹은 관련 에이전트 모듈) 내에서 시스템 프롬프트를 구성하는 로직을 찾습니다.
* 기존 `BookStack` 을 호출하던 로직을 제거(또는 주석처리/우회)하고, `PolicyComposer` 인스턴스를 통해 `compose(...)` 한 다이나믹 정책 텍스트를 `system_prompt` 로 사용하도록 코드를 리팩토링합니다.
* `target_version` 과 해당 에이전트의 역할 문자열이 `target_purposes` 에 알맞게 전달되도록 파라미터를 연결합니다.

## 3. 검증 (Validation)
* 런타임에서 실제로 특정 에이전트(예: `arti_reviewer`)를 기동하거나 TUI 상에서 L1 프리뷰 전송 시, 에이전트의 System Prompt에 로컬 마크다운 병합결과가 제대로 주입되었는지 확인합니다.
