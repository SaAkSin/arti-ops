# 🎨 [DESIGN] arti-ops v0.5.0 TUI 디자인 시스템 명세서

## 1. UI/UX 개요
arti-ops는 웹 브라우저를 띄우지 않고 터미널 환경에서 완벽하게 동작하는 대화형 TUI(Text User Interface) 플랫폼입니다.
화면 깜빡임 없이 유려한 애니메이션과 한글 입력(Native IME)을 지원하기 위해 `rich`와 `prompt_toolkit` 라이브러리를 결합한 하이브리드 인터페이스를 제공합니다.

## 2. 전역 시스템 색상 (TUI Color Palette)

### 2.1. 컨테이너 및 배경
* **Main Console:** 터미널 네이티브 기본 배경색 사용 (`transparent`)
* **Dialog Container:** `bg:#2b2b2b` (다크 톤의 무채색 그레이)
* **Dialog Body:** `bg:#2b2b2b #dddddd` (다크 배경에 밝은 회색 텍스트)
* **Bottom Toolbar:** `bg:#333333 #ffffff`

### 2.2. 시맨틱 포인트 컬러
* **성공 및 포커싱 (Green):** `#00aa00` (목록 선택 시), `green` (완료 메시지, 체크박스)
* **진행 및 알림 (Cyan):** `cyan` (진행 중인 스피너, 주요 시스템 메시지), `#00ffff` (다이얼로그 타이틀 바 강조)
* **경고 및 도구 (Yellow):** `yellow` (LLM 도구 호출 이벤트 출력, 위키 업데이트 필요 경고 목록)
* **에러 및 거절 (Red):** `red` (치명적 오류, 승인 반려, 조기 종료 메시지)

## 3. 핵심 화면 레이아웃 (Layout Structure)

### 3.1. 메인 파이프라인 뷰어 (`./src/arti_ops/cli/main.py`)
전체 화면을 위에서 아래로 부분적으로 갱신하는 단일 흐름 스크린으로 구성합니다.
* **Top Header:** 프로젝트 식별자와 현재 대상 에이전트 정보가 담긴 `rich.Panel`
* **Middle Live Tree:** 에이전트별 작업 단계(Profiler -> Architect -> Verifier -> Executor)를 트리의 브랜치 형태로 실시간 렌더링. 하위 작업 지연 시 라이브 스피너 애니메이션 적용.
* **Bottom Prompt:** 화면 하단에 고정된 프롬프트 입력창. 단축 매크로 힌트(`s`, `r`, `u`, `l`, `q`) 제공.

### 3.2. 대화형 모달 및 리스트 뷰어 (`./src/arti_ops/cli/list_viewer.py`)
자산(Rules, Skills, Workflows) 목록 탐색이나 미리보기를 위해 진입하는 풀스크린 Split 뷰어.
* **Left Pane (40px 비율):** 항목이 디렉토리 계층적으로 표시되는 탐색 트리 구역. 포커스 시 초록색상을 반전 적용.
* **Right Pane (Flexible):** 파일별 마크다운 문서 등 내용을 보여주는 스크롤 가능 텍스트/렌더링 영역.
* **Footer Toolbar:** 뷰어 하단에서 `[↑/↓: 이동 | Space: 미리보기 | Tab: 뷰 전환 | q: 닫기]` 등 동작 가능한 키바인딩을 직관적으로 안내.

## 4. 컴포넌트 에셋 위치
- 메인 TUI 컨트롤러: `./src/arti_ops/cli/main.py`
- 다이얼로그 뷰어 컨트롤러: `./src/arti_ops/cli/list_viewer.py`
