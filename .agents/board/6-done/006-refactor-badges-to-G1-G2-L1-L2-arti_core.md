---
Agent: arti_core
DependsOn: 005
---
# Ticket 006: Refactor Badges to G1/G2/L1/L2 and Add Global Workflows Scan

## 1. 목적 (Objective)
기존 L1, L2, L3로 단순 혼용되던 원격/로컬 뱃지 시스템을 아키텍처 재설계(PRD/SSD 갱신)에 따라 **G1, G2, L1, L2** 구조로 변경합니다. 더불어 사용자의 전역 로컬 워크플로우 디렉토리를 물리적으로 스캔하여 리스트 뷰어에 표시하는 기능을 신규 편입합니다.

## 2. 작업 상세 (Tasks)
1. **[리스트 뷰어 물리적 렌더링 명칭 갱신]**
   - `src/arti_ops/cli/list_viewer.py` 의 `get_missing_pages` 등 함수 내에서 내부 정책 식별 로직 중 원격 위키 매핑 값을 `L1` -> `G1`, `L2` -> `G2`로 전면 교체합니다.
   - 로컬 파일(`.agents/`) 렌더러에 부여하던 기존 `[L3]` 뱃지를 `[L2]` 뱃지 출력으로 일괄 변경합니다.
   
2. **[L1 로컬 전역 스캔 로직 추가]**
   - `list_viewer.py` 내 `workflows` 탐색 로직 등에서 로컬 앱데이터 디렉토리 `~/.gemini/antigravity/global_workflows/` 를 추가 스캔합니다. (`os.path.expanduser` 활용)
   - 해당 디렉토리에 존재하는 마크다운 파일들을 읽어 `[L1]` 뱃지와 함께 `★ Workflows:` 목록에 합병(Append)합니다. (만약 경로가 존재하지 않으면 건너뜁니다)
   - L1(로컬 전역) 파일은 로컬 파일이므로 선택 시 `_load_preview`에서 원격 URI 파싱이 아닌 실제 파일 I/O로 우측에 내용이 로드되어야 합니다. (이미 기존 파일 읽기 로직이 커버할 것이나 경로 구조를 일치시킬 것)

3. **[검증 (Validation)]**
   - `uv run arti-ops` 명령어 실행 후, L1/L2/G1/G2의 UI 뱃지가 직관적으로 렌더링 되는지 육안 확인.
   - `[L1]` 뱃지가 달린 글로벌 워크플로우(예: `arti-pm.md`)가 정상적으로 조회되는가.

## 3. 타겟 변경 파일
- `src/arti_ops/cli/list_viewer.py`
