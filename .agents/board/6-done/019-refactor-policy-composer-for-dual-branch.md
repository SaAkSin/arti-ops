---
Assignee: arti_core
Status: backlog
DependsOn: 018
---

# 📝 Ticket 019: `PolicyComposer` 다중 로드 경로 통합 지원

## 1. 개요 (Objective)
기존 글로벌 경로 기반 문서를 파싱하던 `PolicyComposer`가 `policies/G1` 및 `policies/G2` 디렉토리를 모두 순회하며 지식을 통합하게 구성합니다.

## 2. 세부 요구사항 (Requirements)
* `src/arti_ops/core/policy_composer.py`의 `_load_documents`를 수정합니다.
* `~/.arti-ops/policies/` 하위에서 파싱하던 로직을 세분화하여, `~/.arti-ops/policies/G1` 폴더와 `~/.arti-ops/policies/G2` 폴더를 개별적으로 스캔하여 `PolicyDocument` 리스트에 탑재합니다.
* 내부 `compose()` 조합기의 우선순위 로직에 변동은 없이, 그대로 `scope` 기준으로 정렬되어 프롬프트가 병합되는지 확인합니다. (G1 -> G2 -> L1 순)
* (옵션) `PolicyDocument` 모델이 파일 경로뿐만 아니라 `G1`, `G2`, `Local` 등의 출처(Source)를 판별할 수 있으면 디버깅 로깅에 도움이 될 수 있습니다.

## 3. 검증 (Validation)
* `PolicyComposer` 강제 호출 시 `[G1]` 정책과 `[G2]` 정책이 순차적으로 정렬되어 하나의 `dynamic_policy` 텍스트로 합쳐지는지 확인.
