---
trigger: always_on
---

# graphify

이 프로젝트는 `graphify-out/` 경로에 graphify 지식 그래프를 포함하고 있습니다.

## 규칙

- 아키텍처나 코드베이스 관련 질문에 답변하기 전에, `graphify-out/GRAPH_REPORT.md` 파일을 읽고 갓 노드(god nodes)와 커뮤니티 구조를 확인하십시오.
- `graphify-out/wiki/index.md` 파일이 존재할 경우, 원본(raw) 파일을 직접 읽는 대신 해당 위키를 탐색하십시오.
- graphify MCP 서버가 활성화되어 있다면, `grep`에 의존하는 대신 `query_graph`, `get_node`, `shortest_path`와 같은 도구를 활용하여 정밀하게 아키텍처를 탐색하십시오.
- 현재 세션에서 코드 파일을 수정한 후에는 `graphify update .` 명령어를 실행하여 그래프를 최신 상태로 유지하십시오 (AST 전용, API 비용 발생하지 않음).
