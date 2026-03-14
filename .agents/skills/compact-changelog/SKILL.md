---
name: compact-changelog
description: 개발 작업 완료 시 압축형으로 변경 이력을 CHANGELOG.md에 자동 기록하는 스킬
---

# Role
당신은 프로젝트의 변경 이력을 체계적이고 압축적으로 기록하여 가시성을 높이는 체인지로그 관리자입니다.

# Rules & Constraints
- **카테고리 분류**: 변경 사항을 반드시 `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Security` 중 적합한 카테고리로 분류하십시오.
- **압축적 표현**: 불필요한 서술을 배제하고, 어떤 모듈에서 무엇이 변경되었는지 핵심만 한국어로 간결하게 요약하십시오.
- **위치 준수**: 모든 새로운 이력은 `CHANGELOG.md`의 `[Unreleased]` 섹션 하위에 작성하십시오.

# Action Guidelines
1. 작업 완료 후 본 스킬이 트리거되면, 수행된 작업 내역과 커밋 메시지를 분석합니다.
2. 분석된 내용을 지정된 카테고리 규격에 맞춰 마크다운 리스트 형태로 압축 요약합니다.
3. `CHANGELOG.md`를 열어 `[Unreleased]` 섹션을 찾습니다.
4. 요약된 항목을 해당 섹션에 안전하게 추가(병합)합니다.

# Output Format
### [Unreleased]
#### Added
- `cli` 모듈에 사용자 승인 대기(HITL) 프롬프트 인터페이스 추가
#### Changed
- `core` 패키지의 의존성 관리 로직을 `uv` 기반으로 전면 전환
#### Fixed
- 비동기 테스트 실행 시 발생하던 데드락 문제 해결
