---
Assignee: arti_core
Status: backlog
DependsOn: None
---

# 📝 Ticket 014: `PolicyDocument` 모델 및 마크다운 파서 구현

## 1. 개요 (Objective)
마크다운 기반 동적 정책 문서들을 파싱하고 관리하기 위한 `PolicyDocument` 데이터 모델을 구현합니다.

## 2. 세부 요구사항 (Requirements)
* `src/arti_ops/core/policy_composer.py` 파일을 신규 생성합니다. (필요 시 파일 내 위치 고려)
* `PolicyDocument` 클래스를 구현합니다.
* YAML 구조를 파싱(Frontmatter)하기 위해 `PyYAML`(`yaml` 모듈)과 정규식을 활용하는 `_parse()` 메서드를 구현합니다.
* 파싱된 메타데이터에 따라 파일의 유형(rule, skill, workflow, general)을 자동 추론하거나 할당하는 기능을 추가합니다.
* `target_version` 과 `target_purposes` 를 검증하는 `is_match()` 메서드를 구현합니다.

## 3. 검증 (Validation)
* 임의의 `.md` 파일을 생성 후 정상적으로 Title, Scope, Purpose, Type이 분리되어 저장되는지 단위 테스트 수행.
* 의존성 패키지 확인(`pip install pyyaml` 등 필요 시 pyproject.toml 갱신 여부 검토).
