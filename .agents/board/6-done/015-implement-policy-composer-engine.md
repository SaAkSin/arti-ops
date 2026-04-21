---
Assignee: arti_core
Status: backlog
DependsOn: 014
---

# 📝 Ticket 015: `PolicyComposer` 엔진 구현

## 1. 개요 (Objective)
`.agents/` 하위의 모든 마크다운 파일들을 동적으로 스캔, 필터링, 정렬하여 단일 프롬프트 문맥으로 조합하는 기능을 구현합니다.

## 2. 세부 요구사항 (Requirements)
* `src/arti_ops/core/policy_composer.py` 에 `PolicyComposer` 클래스를 추가로 구현합니다.
* `_load_documents()` 를 구현하여 `.agents/` 디렉토리를 재귀 탐색(히스토리/로그성 폴더는 스킵)하고 `PolicyDocument` 리스트를 구성합니다.
* 요청받은 에이전트 용도(Purposes) 및 버전(Version)에 맞는 문서들만 필터링하는 `compose(target_version, target_purposes)` 메서드를 작성합니다.
* 룰스(rule) -> 워크플로우(workflow) -> 스킬(skill) 항목 우선순위와 스코프(G1>G2>L1)에 따라 결과를 정렬한 후, 병합된 String 텍스트를 반환하도록 합니다.

## 3. 검증 (Validation)
* `.agents/` 내에 더미 룰과 스킬 파일을 두고 `compose()` 메서드가 올바른 순서로 하나의 긴 마크다운 문자열을 리턴하는지 확인합니다.
