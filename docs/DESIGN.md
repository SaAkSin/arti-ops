# 🎨 [DESIGN] arti-ops UI/UX 및 프론트엔드 명세

## 1. UI 프레임워크 

*   **기반 기술:** `prompt_toolkit` (Python TUI 라이브러리)
*   **환경 제한:** 터미널 콘솔 베이스, Text-based UI.

## 2. 레이아웃 구조 (`list_viewer.py` 기준)

*   **전체 화면 구성 (Full-screen Application)**
    *   **Root Container (HSplit):** 상단의 `body` 영역과 하단의 `toolbar`를 분할.
    *   **Body Container (VSplit):**
        *   **Left Panel (Window):** 폭(width) 40 고정으로 `.agents` 하위의 `rules`, `skills`, `workflows` 및 Docs 파일의 목록을 트랙킹 (포커스됨, `selected` 스타일). 배지(!, *, 공백)를 통해 상태 표시.
        *   **Right Panel (Frame & DynamicContainer):** 선택된 파일의 콘텐츠 렌더링, 수동 편집기능, L1 변환 결과(`diff_text_area` 및 `right_text_area` 스왑 구조 적용).

## 3. 키보드 인터랙션 (Key Bindings)

*   `↑` / `↓` / `PageUp` / `PageDown`: 좌측 패널/우측 패널간 스크롤 매핑.
*   `Enter`: 활성화된 파일의 즉각적인 인라인 텍스트 편집 모드(Edit) 진입.
*   `Ctrl+S`: 파일 저장 후, 배지 상태(Update 등) 동적 갱신.
*   `g`: 현재 선택된 마크다운을 L1 전역 글로벌화 에이전트로 전송, 렌더링 뷰를 미리보기로 스왑 (스피너 애니메이션 제공).
*   `u`: Bookstack Upsert 모드 진행 (Checkbox Dialog 플로팅 렌더링).

## 4. 스타일 가이드

*   **다국어 (Native IME):** 터미널 기본 지원 폰트를 사용하되, 한글 입력 충돌을 최소화하는 하단 프롬프트 구성.
*   **컴포넌트 톤 (Theme):** `prompt_toolkit.styles.Style`
    *   `bottom-toolbar`: 배경 `#333333`, 글자 `#ffffff` (다크모드 터미널 최적화)
    *   `selected`: 활성화 노드 강조 배경 `#00aa00`.
    *   `header`: `bold`, `#00ffff` 컬러 구별.
