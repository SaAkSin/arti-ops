---
Status: 1-backlog
Assignee: @arti_core
DependsOn: None
---

# 004-hybrid-remote-local-list-viewer-arti_core

- **목표:** `bookstack.py`와 `list_viewer.py`를 수정하여 로컬에 디렉토리/파일이 없더라도 원격(BookStack)에 존재하는 항목을 `list_viewer`에 표시하도록 개편합니다.
- **상세 지침:**
  1. `src/arti_ops/tools/bookstack.py`의 `get_upsert_plan()`:
     - `if not os.path.exists(target_dir): continue` 구분을 삭제(또는 우회)하여, 로컬 디렉토리가 없더라도 원격(`existing_pages`)에 있는 항목들을 찾아냅니다.
     - 원격에는 있지만 로컬에는 없는 파일/디렉토리들을 `plan` 배열에 담습니다. 이때 `action`은 `"MissingLocally"` (혹은 적절한 식별자)로 지정합니다.
  2. `src/arti_ops/cli/list_viewer.py`의 `run_list_viewer()`:
     - 기존에는 로컬 디렉토리(`os.path.exists`)가 있어야만 화면의 각 섹션(`rules`, `skills`, `workflows`)을 그렸지만 이제는 `plan_lookup`에서 해당 타입(접두어)의 값이 하나라도 존재하면 섹션을 그리도록 조건을 완화(OR 조건)합니다.
     - 로컬 파일 목록에 더해, 로컬에는 없지만 `plan_lookup`에 존재하는(키 기준) 항목들을 병합(Union)하여 그립니다.
     - `action == "MissingLocally"` 인 경우 UI 뱃지를 `⬇ ` (다운로드 필요/원격 단독) 등으로 부여하여 표시합니다.
  3. 로컬 파일과 원격 전용 파일이 동시에 보일 때 정렬이 어그러지지 않도록 검증하고, 테스트(Pytest 또는 수동 TUI 렌더링 검토)를 완료하십시오.
