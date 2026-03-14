# Changelog

모든 변경 사항은 이 파일에 기록됩니다.
이 프로젝트는 유의적 버전(Semantic Versioning)을 따릅니다.

## [Unreleased]
### Added
- `list_viewer.py` 모듈 신규 추가 및 `l` (list) 명령어 전면 고도화: 텍스트 출력을 넘어 좌우 분할(Split) 방식의 전체화면 대화형 TUI 뷰어를 구현, 방향키(`↑`/`↓`) 목록 탐색 및 스페이스바(`Space`) 파일 내용 미리보기 기능 지원
- `u` (upsert) 명령어를 통한 로컬 에셋(규칙, 스킬)의 BookStack 대화형 동기화 기능 추가 (체크박스 다이얼로그 지원)
- 대화형 TUI 환경(Native IME 기반) 도입 및 `rich`, `prompt_toolkit` 마이그레이션 적용
- `r` (reset) 명령어를 통한 `sessions.db` 캐시 명시적 초기화 기능 추가
- 이전 컨텍스트 재사용 시 `💡 이전 세션(sessions.db) 기억을 불러왔습니다.` 형태의 캐시 히트 메시지 시각화
- `arti-ops` CLI에서 실시간으로 타겟 파일(Skill/Rule) 생성 위치를 파싱해 트리에 마젠타 노드로 안내해주는 기능 추가

### Changed
- GWS Chat 통신을 중간 대기 방식에서 배포 성공 후 단방향 요약 송신 방식으로 간소화
- `.agents/rules/`의 경우 `[Name].md`, `.agents/skills/`의 경우 `[Name]/SKILL.md` 디렉토리 구조 생성으로 매핑 로직 분리

### Fixed
- 사용자가 `y`를 입력해 최종 반영을 지시했음에도 `Deployment Executor`로 넘어가지 못하고 영구 대기(Hang)하던 동시성 Lock 해제 버그(`_pause_event.clear()`) 수정
- PlantUML 렌더링 시 외부 환경에서 혼합 다이어그램 호환성을 보장하기 위한 allowmixing 지시어 결함 패치 적용 문서화
