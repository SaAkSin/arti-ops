# Changelog

모든 변경 사항은 이 파일에 기록됩니다.
이 프로젝트는 유의적 버전(Semantic Versioning)을 따릅니다.

## [Unreleased]

### Added

- `list_viewer.py` `p` 키: 현재 선택된 rule/skill 파일을 대상으로 Profiler→Architect→Verifier 인라인 파이프라인 실행 후 Verifier 보고서를 우측 패널에 표시. `Esc`로 원본 복원. Toolbar 스피너 애니메이션 표시.
- `pipeline.py` `run(inline=True)` 파라미터 추가: Verifier 결과를 HITL 없이 즉시 반환하고 Executor를 건너뜀 (l 뷰어 미리보기 모드 지원)

### Changed

- `agents/profiler.py` 지시문 개선: 로컬 환경 스캔·글로벌 정책 수집·충돌 탐지(Conflict Detection) 3단계 구조로 재정의, 출력 포맷 명세 추가
- `agents/architect.py` 지시문 개선: 로컬 우선 원칙(Override) 및 Context-Aware Adaptation 중심으로 정책 융합 전략 전환, Soft-Merge 방식 명세

## [0.5.2] - 2026-03-16

### Added

- `agents/globalizer.py` L1 전역 정책 변환 전용 ADK `LlmAgent` 신규 추가 (Gemini PRO 모델; Scripts 섹션 예제화 규칙 포함)
- `list_viewer.py` `g` 키: 현재 선택 파일을 L1 전역 정책으로 변환하여 우측 패널에 미리보기. `Esc`로 원본 복원. Toolbar 스피너(`|/-\`) 애니메이션 표시.
- `list_viewer.py` `Ctrl+C` / `⌘+C`: 우측 패널 내용을 macOS 클립보드(`pbcopy`)에 복사
- `list_viewer.py` `l` 뷰어 최초 진입 시 첫 유효 항목 자동 미리보기 로드
- `list_viewer.py` 인라인 파일 편집 기능 추가 (`Enter`: 편집 모드 진입, `Ctrl+S`: 저장, `Esc`: 취소)
- `list_viewer.py` `l` 뷰어 내 `u` 키로 BookStack Upsert 기능 직접 통합

### Changed

- `list_viewer.py` `↑`/`↓` 이동 시 자동 미리보기 (Space 키 제거)
- `list_viewer.py` `Enter` 뷰어 종료 기능 제거 → 좌측 패널 `Enter`로 즉시 편집 모드 진입
- `list_viewer.py` `Tab` 키: EDIT 모드에서 포커스 이동 차단 (타이핑 오동작 버그 수정)
- `list_viewer.py` `u` 체크박스에서 위키와 동일한 `Match` 항목 필터링 (배포 불필요 항목 제외)
- `main.py`/`list_viewer.py` `u`/`l` 다이얼로그 배경색 터미널 기본값으로 통일 (강제 dark bg 제거)
- `main.py`/`list_viewer.py` `u` 실행 패턴을 `app.exit` + Application 루프 재진입 방식으로 전환 (두 Application 충돌 버그 수정)

### Fixed

- `bookstack.py` `execute_upsert()` 내 미정의 `console` 참조 2곳 → `logger`로 교체 (`NameError` 방지)
- `gws_chat.py` `send_summary()` 내 미존재 속성 `self.gws_space_id` 참조를 올바른 `self.check_room_id`로 수정 (런타임 `AttributeError` 방지)
- `pipeline.py` `resume()` 메서드 중복 정의(L61) 제거, 인자명 `action_response`로 통일
- `agents/verifier.py`, `agents/executor.py` 중복 `import get_config` 라인 제거
- `tests/test_pipeline.py` 삭제된 `pipeline.sandbox_tool` assertion 제거
- `tests/test_gws_chat.py` 존재하지 않는 `request_approval()`, `run()` 메서드 호출을 실제 `send_summary()` 기반으로 재작성
- `tests/test_verifier.py`, `tests/test_executor.py`, `tests/test_architect.py`, `tests/test_profiler.py` 낡은 instruction 검증 구문을 현재 코드 기준으로 갱신
