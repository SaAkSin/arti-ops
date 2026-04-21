---
Assignee: arti_core
Status: backlog
DependsOn: None
---

# 📝 Ticket 020: GitOps 단일 복제소 기반 브랜치 스위칭(Branch Switching) 롤백 및 적용

## 1. 개요 (Objective)
잘못 설계되었던 G1/G2 폴더 강제 분할(Dual Clone) 로직을 폐기하고, 원래 의도한 Git의 워크트리 본질(1 Directory, 1 Repo)을 활용하여 워크스페이스 유무에 따라 브랜치를 동적으로 스위칭하는 단일 동기화 체계로 복구합니다.

## 2. 세부 요구사항 (Requirements)
1. **`src/arti_ops/tools/github_sync.py` 교정**:
   * 대상을 `~/.arti-ops/policies/G1`, `G2`로 분할하던 로직을 완전히 삭제하고, 오직 `~/.arti-ops/policies` 단일 폴더만 사용(.git 보관)하도록 원복합니다.
   * 복제 시 `git clone <repo> .` 와 같이 단일 타겟으로 복제합니다. 존재할 경우 `git fetch --all`을 수행합니다.
   * 이후, `workspace_name`이 존재한다면 `git checkout <workspace_name>`을 시도합니다. 만약 해당 브랜치가 원격에 아직 없다면 붕괴(Crash)를 막기 위해 에러를 무시하고, `git checkout main`으로 돌아오도록 안전장치(Fallback)를 구현합니다.
   * 체크아웃 성공 시 `git reset --hard origin/<해당_브랜치>`로 최신화합니다.
2. **`src/arti_ops/core/policy_composer.py` 교정**:
   * `_load_documents` 내부에서 `G1`, `G2` 리스트를 루프 돌던 코드를 삭제하고, 기존처럼 `~/.arti-ops/policies` 단일 디렉토리를 `rglob("*.md")`로 한 번에 스캔하도록 원복합니다.
   * `PolicyDocument` 모델에 주입하던 `source_origin` 은 `Global` 등으로 하나로 통일하거나 제거해도 좋습니다. 문서는 어차피 YAML 내의 `scope` 속성(`G1`, `G2`)에 의해 최종 `compose()` 단계에서 정상적으로 우선순위가 정렬됩니다.

## 3. 검증 (Validation)
* ADK가 구동될 때 `~/.arti-ops/policies` 단일 폴더에서 `fetch` 이후 `checkout main` (혹은 `workspace` 브랜치)가 이뤄지는지 터미널 로그를 확인.
* 이후 `PolicyComposer`가 에러 없이 G1/G2 정책들을 문서 내 메타데이터에 기반해 병합(Compose)해내는지 확인.
