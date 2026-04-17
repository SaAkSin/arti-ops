---
Status: 1-backlog
Assignee: @arti_core
DependsOn: None
---

# 003-fix-bookstack-workflows-sync-arti_core

- **목표:** `src/arti_ops/tools/bookstack.py` 내 BookStack 연동 로직에 `workflows` 지원 추가.
- **상세 지침:**
  1. `fetch_policies()`: 87번째 줄과 138-141번째 줄 로직에서 `["rules", "skills"]` 배열 및 분기 처리에 `workflows`를 추가합니다. (`workflows`는 `rules`와 같이 단일 `.md` 파일 구조입니다.)
  2. `create_workspace_book()`: 236번째 줄 필수 챕터 생성 배열에 `workflows`를 추가합니다.
  3. `get_upsert_plan()`: 288-298번째 줄 `chapters` 및 `targets` 정의에 `workflows`를 추가합니다.
  4. `get_upsert_plan()` 내 비교 파일 파싱(319번째 줄 하단)에서 `rules`와 똑같이 `workflows`에 속한 `.md` 파일들이 `Upsert/Match` 뱃지를 받을 수 있도록 `target_type in ["rules", "workflows"]` 형태로 로직을 통합 및 수정합니다.
  5. 변경 후, 에이전트 무결성 검증(`pytest` 등)에 영향을 미치는지 점검하십시오.
