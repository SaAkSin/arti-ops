---
Assignee: arti_core
Status: backlog
DependsOn: 015
---

# 📝 Ticket 017: GitHub 기반 자동 정책 동기화 모듈 (GitOps) 구현

## 1. 개요 (Objective)
기존 정적 파일 기반의 `PolicyComposer`가 런타임 구동 시 최신 원격 GitHub 저장소(Private 지원)의 정책을 자동으로 동기화(`git clone` 또는 `fetch/reset`)할 수 있게 하여 항상 Source of Truth를 유지합니다.

## 2. 세부 요구사항 (Requirements)
* `src/arti_ops/config.py` 시스템 내 글로벌 인증 정보(`~/.arti-ops/credentials`)를 읽어들이는 룰을 기반으로, `[github]` 하위나 `[default]` 항목에서 `github_policy_repo`, `github_policy_branch`, `github_token` 등의 값을 가져오도록 `get_config()` 또는 `Configurator` 로직과 연동합니다.
* 로컬의 `.agents` 가 아닌 글로벌 정책 저장 경로로서 `~/.arti-ops/policies` 를 기본 대상(`TARGET_DIR`)으로 지정합니다.
* 신규 파일 `src/arti_ops/tools/github_sync.py` 에 `GithubPolicySync` 클래스를 구현합니다.
    * `Token` 기반 HTTPS URL 파싱(`urllib.parse`) 및 마스킹 처리 적용.
    * 파이썬 내장 `subprocess` 모듈을 이용해 `~/.arti-ops/policies/.git` 디렉토리 유무에 따라 `git clone` 및 `git fetch` & `git reset --hard origin/branch` 로직을 분기 처리합니다.
* 기존 `src/arti_ops/core/policy_composer.py` (`PolicyComposer` 클래스)의 `__init__` 메서드를 수정하여:
    1. 동기화 플래그(`auto_sync`)가 `True` 일 때 `GithubPolicySync.sync()`를 먼저 호출하고,
    2. 로컬 프로젝트의 `.agents/` 디렉토리뿐만 아니라 글로벌 `~/.arti-ops/policies/` 디렉토리에 있는 마크다운 파일들까지 함께 스캔하여 병합(compose)하도록 보강합니다.

## 3. 검증 (Validation)
* 잘못된 토큰을 넣었을 때 에러 로그 상에 토큰이 `***TOKEN***` 으로 정상 마스킹되어 나타나는지 확인합니다.
* 올바른 권한이 주어졌을 때, 에이전트를 가동하면 `clone` 또는 `fetch` 후 콘솔에 최신 정책을 성공적으로 병합했다는 로그가 정상 작동하는지 여부를 검증합니다.
