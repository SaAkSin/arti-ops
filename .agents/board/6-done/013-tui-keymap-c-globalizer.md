# 013-tui-keymap-c-globalizer
DependsOn: [012]
AssignedTo: @arti_cli

## 작업 목적
최근 TUI 단축키 개편으로 배포 기능(`g`, `u`)이 통합되면서 제거되었던 기존의 "AI 파이프라인 기반 L1 전역 정책 변환(일반화)" 기능을 복구하고, 이를 새로운 단축키 `c` (Convert)에 할당합니다. 즉, `c`를 누르면 L2 로컬 스킬이 L1 글로벌 템플릿 제안으로 우측 패널에 스트리밍되어야 합니다.

## 구현 요건
1. **`list_viewer.py` 툴바 가이드 수정**:
   - `update_toolbar()` 내에 `c_hint = " | c: L2 -> L1 변환" if is_agents else ""` 구문을 추가하고 툴바 메시지에 노출시킵니다.
2. **`list_viewer.py` 단축키 바인딩 블록 구성**:
   - `c` 키 입력을 감지하는 `@kb.add("c", filter=Condition(lambda: not is_edit_mode and is_agents))` 구문을 작성합니다.
   - 우측 패널의 스킬 파일 콘텐츠(`right_text_area.text`)를 읽어와 `Runner(agent=get_globalizer_agent())`를 호출하여 변환을 스트리밍하는 `async def _do_l1_convert()` 로직(이전 커밋 백업 또는 동일 로직 재작성)을 복구하여 바인딩합니다.
3. **스타일링**: 변환 진행 중 하단 툴바에 진행률 애니메이션 스피너(`| / - \`)가 동일하게 회전해야 합니다. 

## 자율 검증 기준 (Ralph Loop)
- `.agents/skills` 디렉토리 하위의 마크다운 파일을 우측에 띄워둔 상태에서 `c` 입력을 감지하는가.
- 누르는 즉시 `L1 변환 중...` 스피너가 돌며, AI 응답값이 우측 패널 텍스트 에어리어에 실시간으로 작성되는가.
- 시각적인 UI 변경(신규 키 및 스트리밍 확인)이 수반되므로 테스트 후 `5-pending_approval`에서 인간의 승인을 대기해야 함.
