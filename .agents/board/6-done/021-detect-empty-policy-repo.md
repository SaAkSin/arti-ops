---
Assignee: arti_core
Status: backlog
DependsOn: None
---

# 📝 Ticket 021: `GithubPolicySync` 빈 저장소 상태(Is_Empty) 감지 로직

## 1. 개요 (Objective)
원격 Git 저장소를 최초로 연결했을 때, 아직 아무런 커밋도 없는 깡통 저장소인 경우 `git clone`은 성공하지만 브랜치가 생성되지 않아 이후 `checkout main` 로직에서 Crash가 날 수 있습니다. 이를 방어하고, 파이프라인 외부로 "현재 이 저장소는 텅 비어있다"는 상태를 전달할 수 있도록 리팩토링합니다.

## 2. 세부 요구사항 (Requirements)
* `src/arti_ops/tools/github_sync.py`를 수정합니다.
* `GithubPolicySync` 클래스에 `is_empty_repo` 속성을 추가하고 `False`로 초기화합니다.
* `sync()` 로직 내에서 클론 이후에 `git branch -a` 또는 `git status` 등을 호출하여 커밋이 하나도 존재하지 않는지(에볼루션 이전 상태) 감지합니다. 
* 만약 비어있는 상태라면 `self.is_empty_repo = True`로 설정하고 에러를 띄우는 대신 조용히 성공(`True`)으로 리턴하여 파이프라인이 정상적으로 TUI 뷰어로 진입하도록 예외 처리합니다.
* `Configurator`나 `PolicyComposer`가 этот 속성을 가져갈 수 있는 방법(Property Getter)을 마련해줍니다.

## 3. 검증 (Validation)
* 빈 깡통 계정의 원격 URL을 주입했을 때, `sync()`가 에러 스택을 남기지 않고 단지 Info 로고("빈 저장소가 감지되었습니다")를 뿌린 뒤 워크플로우를 통과시키는지 확인.
