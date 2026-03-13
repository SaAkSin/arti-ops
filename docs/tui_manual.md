# 🖥️ arti-ops TUI 모듈 사용 설명서 (`tui_manual.md`)

`arti-ops` 플랫폼은 CLI 환경에서 다중 에이전트(Multi-Agent)들의 릴레이 워크플로우를 모니터링하기 위해 TUI (Text User Interface)를 지원합니다.
최신 Claude CLI, Aider 등의 스타일을 차용한 **채팅-말풍선(ChatBubble)** 형태의 인터페이스를 갖추고 있어 지루한 터미널 텍스트 로그 대신 대화형으로 진행사항을 파악할 수 있습니다.

---

## 1. TUI 실행 방법 (동기화 파이프라인 가동)

타겟 프로젝트(Workspace)의 L1/L2 정책을 융합하고, 로컬 디렉토리에 시뮬레이션 및 배포를 수행하는 전체 파이프라인을 가동하려면 `arti-ops sync` 명령어를 터미널에 입력합니다.

### 📌 기본 실행 명령어
```bash
uv run arti-ops sync --workspace <대상-프로젝트-ID>
```

#### 예시: "DEMO-W-999" 프로젝트에 대한 룰 동기화 진입
```bash
uv run arti-ops sync --workspace DEMO-W-999
```

> **Note:**
> 백그라운드에서 Google ADK 기반의 `Runner`가 백그라운드 태스크로 올라가며, LLM 에이전트(Profiler, Architect, Verifier, Executor)가 순차적으로 호출됩니다.
> 해당 과정 중 도출되는 토큰(답변 텍스트)은 TUI 화면에 실시간 마크다운 포맷으로 스트리밍되어 그려집니다.

---

## 2. 화면 구성 요소

TUI 뷰어는 크게 3개의 구역으로 분할됩니다.

1. **상단 Header**: 
   - 실시간 시계와 현재 애플리케이션의 버전(`arti-ops v0.1.0`), 구동 타이틀을 보여줍니다.
2. **중앙 Chat Container (채팅 스크롤 뷰)**:
   - **`⚙️ System`**: 앱 시작, 에이전트 전환, 에러 알림 등 기계적인 상태 천이 정보를 담습니다.
   - **`👤 User`**: 파이프라인에 최초 입력된 명령(프롬프트)나 HITL 개입 등 사용자의 요청 사항을 보여줍니다.
   - **`🤖 Agent Pipeline`**: LLM이 반환하는 추론, 스크립트 작성, 마크다운 문서 등 핵심 결과물을 나타냅니다.
     * 포인트 컬러로 좌측 보더 라인이 생기며, 마크다운 표, 링크, 코드 블럭 등이 터미널 자체 렌더링을 거쳐 출력됩니다.
3. **하단 Footer / Status Bar**:
   - 현재 진행 중인 상태(예: `⏳ Pipeline is running... Please wait.` 또는 `✅ Done!`)를 띄워 백그라운드 진행 여부를 직관적으로 안내합니다.

---

## 3. 단축키 (Key Bindings)

TUI 앱 내에서 지원되는 글로벌 터미널 단축키입니다.

- <kbd>q</kbd> 또는 <kbd>Ctrl</kbd> + <kbd>c</kbd> : 진행 중인 파이프라인을 강제 종료하고, TUI 화면에서 즉시 빠져나옵니다. (Quit)
- <kbd>↑</kbd> <kbd>↓</kbd> (또는 <kbd>PageUp</kbd> <kbd>PageDown</kbd>, 마우스 스크롤) : 에이전트가 반환한 긴 답변을 읽거나 위로 올려볼 때 뷰를 스크롤 할 수 있습니다.

---

## 4. 트러블슈팅 및 로그 추적

- **Q. TUI 화면에서 에러 메세지가 출력되며 강제 종료됩니다.**
  - `⚙️ System [Error Occurred]` 버블에 출력되는 마크다운의 파이썬 예외 트레이스를 먼저 살펴주세요. 환경변수(`GEMINI_API_KEY` 등)나 외부 패키지(`docker`)가 없는 경우가 가장 흔합니다.
  - TUI를 통하지 않은 원시 에러 로그가 필요할 땐 `logs/` 디렉토리 내에 쌓인 `pytest.log` 나 관련 에이전트 로깅 파일을 열어 상세 원인을 추적하면 됩니다.
