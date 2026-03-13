# 🧪 arti-ops v0.1.0 테스팅 가이드

이 문서는 `arti-ops` 프로젝트의 유닛 테스트 구성 및 실행 방법을 안내합니다. 모든 테스트 메커니즘은 `pytest`와 `pytest-asyncio`를 기반으로 동작하며, 외부 API 및 시스템 의존성을 분리(Mocking)하여 안정적으로 수행되도록 설계되었습니다.

## 1. 테스트 환경 구성 및 패키지 설치

`uv` 패키지 매니저를 활용하여 프로젝트 본체 및 의존성과 테스트 도구를 함께 설치합니다.

```bash
# 프로젝트 의존성 동기화 및 테스트 도구 추가 (최초 1회)
uv sync
uv add pytest pytest-asyncio
```

## 2. 테스트 디렉토리 구조

로컬 테스트 케이스들은 `tests/` 폴더 내에 작성되며, 모듈(Component)별로 파일을 분리하여 관리합니다.

```text
arti-ops/
 └── tests/
      ├── test_bookstack.py       # BookStack API Mock 기반의 응답/에러 엣지 케이스 테스트
      └── test_bookstack_live.py  # .env로 주입된 실 토큰 기반의 BookStack 연동 테스트
```

## 3. 테스트 실행 방법

가상 환경 내부망에서 안전하게 테스트 스크립트를 일괄 동작시키려면 다음 명령어를 사용하십시오.

```bash
# 전체 테스트 실행 (결과 로그는 logs/pytest.log 파일로 자동 생성됨)
uv run pytest tests/

# 특정 파일만 지정해서 실행 (예시: bookstack_toolset)
uv run pytest tests/test_bookstack.py

# 테스트 결과의 상세 정보(-v)와 표준 출력 디버깅(-s)을 함께 보기
uv run pytest -v -s tests/
```

> [!NOTE]
> `pyproject.toml` 설정에 따라 모든 테스트의 실행 로그는 `logs/pytest.log` 파일에 디버그(DEBUG) 레벨로 기록됩니다. 각 테스트별 응답값이나 API 통신 오류를 자세히 추적할 때 유용합니다.

## 4. 주요 테스트 모듈 설명

### 4.1. `test_bookstack.py`
BookStack(사내 위키) API 리소스를 읽어 오거나 결과물을 업로드(Publish)하는 `BookStackToolset` 의 동작 성공 여부를 검증합니다. 
통신 지연 혹은 토큰 만료의 이슈를 배제하기 위해 `pytest.fixture`의 `httpx`를 통해 환경변수 및 응답 객체들을 가짜(Mocked) 데이터로 오버라이드하여 동작시킵니다.
에이전트 구현 로직에 맞춰 **하나의 Scope을 조회할 때 `rules` 페이지와 `skills` 페이지를 순차적으로 크롤링하여 합치는 로직이 테스트에 반영**되어 있습니다.

*   **`test_fetch_policies_global`**: 전사 공통 가이드(L1) `rules`와 `skills` 조회 로직 통합 검증.
*   **`test_fetch_policies_workspace_success`**: 워크스페이스 전용 룰(L2)의 성공적 조회 검증.
*   **`test_fetch_policies_workspace_missing_id`**: 워크스페이스 조회 시 필수 파라미터가 비어있을 때 발생하는 예외 에러 반환 검증.
*   **`test_publish_sync_report`**: 배포 이후 구성된 Diff 데이터를 '릴리즈 노트' 페이지로 Update 퍼블리싱하는 과정 검증.

### 4.2. `test_bookstack_live.py`
Mocking을 거치지 않고, 로컬 시스템의 `.env`에 정의된 `BOOKSTACK_TOKEN_ID` 와 Secret을 활용하여 실제 BookStack 웹과 라이브(Live) 비동기 통신을 테스트합니다. 
만약 `.env` 에 관련 키가 없다면 `@pytest.mark.skipif` 에 의해 자동으로 테스트가 스킵됩니다.

## 5. 추가 테스트 작성 (진행중인 사항)

향후 개발될 Agent 4종(`Profiler`, `Architect`, `Verifier`, `Executor`)에 대해서도 프롬프트 인스트럭션 추론 결과 및 State 머신의 변화를 추적(Mocking LLM)하는 단위 테스트가 `tests/test_agents.py` 등으로 지속 추가될 예정입니다.
