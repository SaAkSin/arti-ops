---
Assignee: arti_core
Status: backlog
DependsOn: 021
---

# 📝 Ticket 022: TUI 내 'i' 키 기반 빈 저장소 부트스트랩(Cold Start)

## 1. 개요 (Objective)
`Ticket 021`에서 감지한 `is_empty_repo` 플래그를 받아, TUI (`list_viewer.py`) 접속 시 사용자에게 "최초 저장소 부트스트랩을 위해 i를 누르세요"를 안내하고, `i` 키를 통해 G1 정책 첫 커밋을 생성합니다.

## 2. 세부 요구사항 (Requirements)
* `src/arti_ops/cli/list_viewer.py`를 수정합니다.
* 빈 저장소 트리거 플래그(`is_empty_repo`)가 `True`일 경우:
  * 좌측 메뉴 아이템에 강제로 `[G1] ⚠️ 저장소가 비어있습니다. 'i' 키를 눌러 G1 정책을 작성하고 초기화하세요.` 라는 항목을 주입합니다.
  * 단축키 `i`를 신규 바인딩합니다 (빈 저장소일 때만 활성화). 해당 키를 누르면 우측 영역(TextArea)이 빈 문서 편집기 상태(`is_edit_mode = True`)로 전환됩니다.
  * 이때 문서의 기본 템플릿 텍스트를 다음과 같이 세팅해주십시오.
    ```markdown
    ---
    scope: G1
    type: System
    purpose: all
    title: Global Master Rule
    ---
    여기에 첫 번째 G1 원칙을 자유롭게 작성해 주세요...
    ```
* 사용자가 `Ctrl+S`로 저장 시, 이것이 '최초 부트스트랩' 프로세스라면 `~/.arti-ops/policies/G1_Master.md` 경로에 파일을 물리적으로 쓰고, `git add .`, `git commit -m "Init G1 policy"`, `git branch -M main`, `git push -u origin main` 의 순서로 `subprocess` 명령을 쏘아 올려 원격 저장소에 반영합니다.
* 성공 시 `is_empty_repo` 상태를 `False`로 풀고, TUI 재구동 또는 메시지 렌더링.

## 3. 검증 (Validation)
* 빈 폴더로 위장한 Mock 상태에서 `list_viewer.py`를 구동한 뒤 `i` 키를 눌러 문서 수정 상태로 진입하는지 확인.
* `Ctrl+S`를 눌렀을 때 지정된 커밋 명령어가 터미널 스택에 떨어지는지 콘솔 로그 확인.
