# 012-tui-keymap-upsert-split
DependsOn: [None]

## 작업 목적
TUI `l` 명령어의 하단 단축키(명령어) 중 BookStack 배포 및 전역화 역할을 담당하던 `u`와 `g` 명령어의 책임을 명확히 분리 재정의합니다.
- `u` 키: 로컬 워크스페이스 스킬(L2)을 BookStack의 워크스페이스 글로벌 정책(G2)으로 배포(Upsert)하도록 한정합니다.
- `g` 키: 기존 파이프라인(L1 변환) 대신, 로컬 전역 스킬(L1)을 BookStack의 마스터 글로벌 정책(G1)으로 배포(Upsert)하도록 동작을 변경합니다.

## 변경 요건
1. **담당 에이전트 지정 (필수)**: 
   AssignedTo: `@arti_cli`
2. **`list_viewer.py` 단축키 바인딩 수정**:
   - `u` 키바인딩(489~494번째 줄 영역)의 반환값을 `result="upsert_workspace_requested"` (L2->G2) 명칭으로 구체화하십시오.
   - `g` 키바인딩(616~665번째 줄 영역)에서 기존의 `_do_l1_convert` AI 런타임 가동 로직을 제거하고, `event.app.exit(result="upsert_global_requested")` (L1->G1) 형식으로 `u` 키와 동일한 방식의 탈출 구문을 적용하십시오.
3. **`list_viewer.py` Application 루프 탈출 후 처리 로직 대응**:
   - `list_viewer.py`의 `run_list_viewer` 에 위치한 Application 종료 후 처리부(886번째 줄 부근)에서 다이얼로그 호출 분기를 나누십시오.
   - `result == "upsert_workspace_requested"`: 기존의 `show_upsert_dialog`로 넘기되 스코프 등(L2 -> G2 전용)을 처리할 수 있게 분기합니다.
   - `result == "upsert_global_requested"`: L1 파일을 BookStack의 글로벌 스페이스(G1)로 배포하기 위한 다이얼로그 로직으로 분기하여 재진입 처리를 지원하도록 수정하십시오.

## 자율 검증 기준 (Ralph Loop)
- TUI 화면에서 우측 파일 `[L2]` 스킬을 띄우고 `u`를 누르면 BookStack Workspace(G2) 배포 다이얼로그로 넘어가는지 확인.
- 우측 파일 `[L1]` 환경에서 `g`를 누르면 BookStack Global(G1) 배포 다이얼로그로 정상적으로 넘어가는지(기존 스피너 동작이 아니라) 확인.
