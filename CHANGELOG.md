# Changelog

모든 변경 사항은 이 파일에 기록됩니다.
이 프로젝트는 유의적 버전(Semantic Versioning)을 따릅니다.

## [Unreleased]

### Added

- `list_viewer.py` `l` 뷰어에 `u` 키로 BookStack Upsert 기능 직접 통합: `checkboxlist_dialog`로 항목 선택 후 배포. 배포 완료 항목 배지 즉시 `Match`로 갱신. toolbar에 `u: 위키 배포` 힌트 자동 표시.
- `list_viewer.py` 함수 시그니처에 `full_plan`, `bookstack`, `upsert_style` 추가, `main.py` 호출부에 `pt_style` 전달하여 `u`/`l` 다이얼로그 색상 일치.

- `tests/test_architect.py`, `tests/test_profiler.py` 낡은 instruction 문자열 검증을 현재 코드 기준으로 갱신
- `u` (upsert) 명령어를 통한 로컬 에셋(규칙, 스킬)의 BookStack 대화형 동기화 기능 추가 (체크박스 다이얼로그 지원)
- 대화형 TUI 환경(Native IME 기반) 도입 및 `rich`, `prompt_toolkit` 마이그레이션 적용
- `r` (reset) 명령어를 통한 `sessions.db` 캐시 명시적 초기화 기능 추가

### Changed

- 위키 연동 현황 표기를 단순 파일 유무 방식(`N`, `U`)에서 실제 마크다운 내용 1:1 병렬 대조(Match) 방식으로 고도화하고, 직관적인 신규 심볼(`!` 신규, `*` 변경됨, ` ` 완벽 일치/수정불필요) 도입
- `u` (upsert) 명령어 체크박스 다이얼로그의 색상을 터미널 기본 다크 테마와 이질감 없게 조화로운 배색으로 스타일링 통합
- CLI 콘솔 내 호환성 및 출력 깨짐 문제를 해결하기 위해 시스템 안내 메시지 및 트리의 모든 이모지 기호를 모던 기하학 ASCII 도형(▶, ■, ◎, √ 등)으로 전면 교체
- BookStack API 호출 등 동기화 관련 장기 대기 프로세스들에 `rich.console.status` 기반의 동적 로딩 스피너(dots) 애니메이션 일괄 적용
- GWS Chat 통신을 중간 대기 방식에서 배포 성공 후 단방향 요약 송신 방식으로 간소화
- `.agents/rules/`의 경우 `[Name].md`, `.agents/skills/`의 경우 `[Name]/SKILL.md` 디렉토리 구조 생성으로 매핑 로직 분리

### Fixed

- `gws_chat.py` `send_summary()` 내 미존재 속성 `self.gws_space_id` 참조를 올바른 `self.check_room_id`로 수정 (런타임 `AttributeError` 방지)
- `pipeline.py` `resume()` 메서드 중복 정의(L61) 제거, 인자명 `action_response`로 통일
- `agents/verifier.py`, `agents/executor.py` 중복 `import get_config` 라인 제거
- `tools/bookstack.py` 미정의 `console` 객체 사용 2곳 → `logger.error()` / `logger.warning()`으로 대체 (NameError 방지)
- `tests/test_pipeline.py` 삭제된 `pipeline.sandbox_tool` assertion 제거
- `tests/test_gws_chat.py` 존재하지 않는 `request_approval()`, `run()` 메서드 호출을 실제 `send_summary()` 기반으로 재작성
- `tests/test_verifier.py`, `tests/test_executor.py` 낡은 instruction 문자열 검증 구문을 현재 코드 기준으로 갱신
