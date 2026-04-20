# 008-tui-diff-lazy-loading
DependsOn: [007]

## 작업 목적
`main.py`의 `asyncio.gather`를 통해 `global`, `workspace` 정책을 선행 로딩(Pre-fetching)하는 무거운 네트워크 작업을 제거하고, TUI 화면에서 실제 정책 비교(Diff)가 요구되는 시점이나 `(Remote)` 마커 조회가 꼭 필요할 때만 API를 지연 호출(Lazy Loading)하도록 구조적 최적화를 수행합니다.

## 변경 요건
1. `src/arti_ops/cli/main.py` 내부 `l` 커맨드 분기에서 `bookstack.fetch_policies`를 무조건 2회 호출하는 부분을 걷어냅니다. (단, `plan`을 가져오는 `bookstack.get_upsert_plan` 만 초기 렌더링을 위해 유지)
2. `src/arti_ops/cli/list_viewer.py` 내부에서 캐시가 없을 경우에 한해 Diff 뷰어([d] 또는 [D] 동작 시)나 `_load_preview()`가 호출될 때 로딩 스피너와 함께 fetch 하도록 lazy 템플릿 렌더링 로직으로 이관하십시오. (이미 Diff 함수 내에는 Lazy Fallback 코드의 기초 형태가 존재하고 있습니다.)

## 검증 방법
- 기존 `[L1]`, `[L2]` 및 `(Remote)` 목록이 정상 렌더링되는지 확인합니다.
- `d` (Diff) 키를 누르기 전에는 불필요한 백그라운드 API 호출이 발생하지 않는지 네트워크 로깅을 통해 검증합니다.
- 첫 `l` 명령어 진입 속도가 캐시가 아예 없는 빈 상태에서도 기존 대비 50% 이상 획기적으로 개선되어야 합니다.
