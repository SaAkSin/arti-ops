---
Agent: arti_core
DependsOn: 004
---
# Ticket 005: Hierarchical L1/L2/L3 Remote Preview List Viewer

## 1. 목적 (Objective)
TUI 리스트 뷰어에서 카테고리(Rules, Skills, Workflows) 하위의 항목들에 대해 [L1], [L2], [L3] 뱃지를 부착하여 계층적 출처를 시각화하고, 로컬 디스크에 파일이 없는 Remote 전용([L1], [L2]) 항목 선택 시 `_policy_cache`에서 직접 파싱하여 우측 패널에 실시간 프리뷰를 렌더링하도록 `list_viewer.py` 로직을 개선합니다.

## 2. 작업 상세 (Tasks)
1. **[계층형 UI Badge 도입]**
   - `src/arti_ops/cli/list_viewer.py` 의 리스트 아이템 노출부(display_text 작성)를 개선합니다.
   - 물리적 로컬 디스크에 존재하는 파일: `[L3]` 뱃지 부착.
   - `plan_lookup` 결과 `MissingLocally`에 해당 (Workspace 위키에만 존재): `[L2]` 뱃지 부착.
   - Workspace에도 없고 Global 위키 정규식에서만 파싱된 원격 전용 파일: `[L1]` 뱃지 부착.
   *(팁: `get_missing_pages()` 구조를 리스트 대신 식별용 딕셔너리로 전환하면 렌더링 시 분류하기 편합니다.)*
   
2. **[원격 캐시 실시간 Preview 랜더링]**
   - 하단 키맵 리스너 혹은 포커스 이동 이벤트 핸들러(`_load_preview` 또는 이와 유사한 역할의 함수)를 수정합니다.
   - `file_path`가 `None`이거나 존재하지 않는 경로일 때 즉시 포기하지 않고, `display_text`나 내장 메타데이터를 통해 해당 객체가 원격 객체임을 인지합니다.
   - `_policy_cache.get("global")` 또는 `workspace` 캐시 텍스트 내에서, 해당 파일의 이름(예: `### arti-auto`)으로 정규식 텍스트 추출을 수행하여 우측 엑스트라 패널에 마크다운 렌더링 텍스트를 공급합니다.
   
3. **[검증 (Validation)]**
   - `uv run arti-ops` 및 `l` 뷰어로 진입하여 에러가 발생하지 않는지 확인.
   - L1 전용 항목을 키보드 방향키로 선택했을 때 정상적으로 L1 워크플로우 명세서 본문이 나타나는가.

## 3. 타겟 변경 파일
- `src/arti_ops/cli/list_viewer.py`
