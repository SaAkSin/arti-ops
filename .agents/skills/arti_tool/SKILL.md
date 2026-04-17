---
name: arti_tool
description: 외부 연결점(BookStack, GWS) 및 로컬 파일 시스템 제어 툴셋 연동 에이전트.
---
# arti_tool 가이드라인

1. **역할:** `BookStackToolset` (워크플로우/정책), `GwsSummaryTool` 등 외부 문서를 가져오거나 동기화시키는 도구 모듈들을 다룹니다.
2. **격리 규칙:** 
   - `.agents/worktrees/arti_tool` 내부에서만 개발을 진행하십시오.
   - 로컬 테스트 수행 시 `.agents/scripts/ralph-loop.sh arti_tool <티켓명>`을 실행하십시오.
