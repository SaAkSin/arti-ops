---
Assignee: arti_core
Status: backlog
DependsOn: None
---

# 📝 Ticket 018: `GithubPolicySync` 듀얼 브랜치(G1/G2) 동기화 리팩토링

## 1. 개요 (Objective)
단일 브랜치를 클론하던 `GithubPolicySync`를 수정하여, 글로벌(G1) 전용 경로와 워크스페이스(G2) 전용 경로를 나누어 각각 `main` 브랜치와 `workspace name` 브랜치를 동시 동기화하도록 리팩토링합니다.

## 2. 세부 요구사항 (Requirements)
* `src/arti_ops/tools/github_sync.py`를 수정합니다.
* `get_project_id()`(또는 현재 경로 이름)를 가져와 워크스페이스 이름을 식별합니다.
* 기존 단일 타겟 `~/.arti-ops/policies` 경로를 다음 두 개로 분할합니다.
  1. `~/.arti-ops/policies/G1`: (branch: `main`) 동기화 타겟.
  2. `~/.arti-ops/policies/G2`: (branch: `{workspace_name}`) 동기화 타겟.
* `sync()` 메서드에서 두 브랜치에 대해 각각 Clone / Fetch 루프를 수행하게 만듭니다.
* **[🚨 예외 처리 방어]** 새로운 워크스페이스의 경우 G2용 외부 브랜치가 아직 GitHub에 존재하지 않을 수 있습니다. `git` 명령어가 실패하더라도 전체 에이전트 파이프라인이 붕괴하지 않도록 안전하게 `try-except` 처리하고, "해석: G2 브랜치가 아직 생성되지 않았으므로 패스합니다" 라는 취지의 경고 로그만 찍도록 방어 코드를 작성하십시오.

## 3. 검증 (Validation)
* 빈 깡통 로컬 저장소에서 실행했을 때, `main` 브랜치만 `policies/G1` 경로에 성공적으로 클론되고 G2 동기화는 부드럽게 무시/실패 처리되는지 터미널 출력 확인.
