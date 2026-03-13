---
name: maintain-architecture
description: arti-ops 프로젝트의 디렉토리 구조를 파악하고, 새 파일을 생성하거나 코드를 리팩토링할 때 아키텍처의 일관성을 유지하기 위해 사용합니다.
---

# Role

당신은 `arti-ops` 프로젝트의 아키텍처와 디렉토리 구조를 엄격하게 수호하는 관리자(Agent)입니다. 프로젝트 내에서 파일 생성, 이동, 리팩토링 작업을 수행할 때 반드시 이 문서의 규칙을 준수하십시오.

# Project Overview

이 프로젝트는 AI 에이전트(Antigravity)의 Rule, Skill, Workflow를 BookStack(사내 위키)에서 중앙 통제하고 자동 병합 및 배포하는 **지능형 CLI/TUI 환경(AgentOps 플랫폼)**입니다. Python(Textual, Google ADK)을 기반으로 구동되며 `uv`를 통해 의존성을 엄격히 격리 관리합니다.

# Directory Architecture & Rules

## 1. Root Directory (`/`)

프로젝트 환경 정보, 설정 및 루트 명세가 위치하는 영역입니다.

- **`PRD.md`, `SSD.md`**: 제품 및 시스템 아키텍처 요구사항 정의서. 기능 추가 시 우선적으로 기준이 되는 문서들입니다.
- **`.env`**: 시스템 실행 및 외부 API(BookStack, GWS Chat, Gemini) 연동 환경 변수.
- **`pyproject.toml` & `uv.lock`**: `uv`를 이용한 Python 의존성 관리 명세. CLI 진입점(`[project.scripts]`) 설정 포함.
- **🚫 제약사항**: 파이썬 패키지를 추가할 때 글로벌 `pip`를 사용하지 말고, 항상 `uv add <package>` 명령을 사용해 `pyproject.toml`에 명시적으로 반영되도록 하십시오. OS 레벨과 완벽히 격리된 환경을 보장해야 합니다.

## 2. Source Code (`src/arti_ops/`)

핵심 비즈니스 로직 및 TUI, 그리고 에이전트 워크플로우가 위치하는 영역입니다.

- **`agents/`**: ADK 기반 메타 에이전트들(`profiler.py`, `architect.py`, `verifier.py`, `executor.py`). 각자의 역할에 따라 `GEMINI_MODEL_PRO` 또는 `GEMINI_MODEL_FLASH` 환경변수를 매핑받아 구동됩니다.
- **`tools/`**: 에이전트가 실제로 호출하여 작업을 수행하는 함수 모음 (`bookstack.py`, `gws_chat.py`, `sandbox.py`). 상속에 주의하여 ADK의 `BaseTool`, `ContainerCodeExecutor` 등을 확장해야 합니다.
- **`core/`**: 에이전트 크루를 엮어주는 파이프라인(Runner) 등 코어 엔진(`pipeline.py`).
- **`cli/`**: 사용자와 상호작용하는 터미널 엔트리 포인트(`main.py`). `Textual` TUI 레이아웃 및 `argparse` 처리가 포함됩니다.
- **🚫 제약사항**: `cli` 레이어가 `agents`나 `tools`를 직접 조작하지 않고 `core` 엔진을 통해 파이프라인에 위임하는 하향식(단방향) 의존성을 유지하십시오. 순환참조(Circular Import)는 엄격히 금지됩니다.

## 3. Tests & Documentation (`tests/`, `docs/`)

플랫폼의 지속 가능한 유지보수를 위한 문서와 테스트 항목이 관리되는 곳입니다.

- **`tests/`**: `pytest` 기반 단위 및 통합 테스트 코드 (`test_bookstack.py` 등). API 통신은 철저히 `monkeypatch`로 환경변수를 Mocking 하여 작성합니다.
- **`docs/`**: `bookstack_guide.md` 등 사용자를 위한 지침 문서.
- **🚫 제약사항**: `tools/`나 `agents/` 내 새로운 객체가 생성될 경우, 동일선 상의 무결성을 증명할 수 있는 비동기(`@pytest.mark.asyncio`) 테스트 코드를 반드시 `tests/` 에 동기화하여 작성하십시오.

# Action Guidelines

1. 사용자가 기능 확장을 요청할 시, 해당 변경점이 진입점(`cli`), 오케스트레이션(`core`), 판단 로직(`agents`), 실제 작업 함수(`tools`) 중 어느 곳에 속하는지 명확히 구분하여 적용하십시오.
2. 코드를 작성하기 전에, PRD 등 기준 문서에 명시된 제약사항(HITL, L1/L2 룰 합의 원칙 등)이 잘 반영될 구조인지 미리 검토하십시오.
3. 새로운 `BaseTool` 클래스를 작성할 시, Pydantic 모델의 `__init__` 동작 방식과 어긋나지 않도록 `kwargs.setdefault("name", ...)` 패턴을 명확히 지켜주십시오.
