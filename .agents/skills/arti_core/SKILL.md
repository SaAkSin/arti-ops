---
name: arti_core
description: 파이프라인 엔진과 AI 에이전트 워크플로우 제어를 위한 핵심 로직 전담.
---
# arti_core 가이드라인

1. **역할:** `Google-ADK` 기반의 파이프라인 뼈대(`pipeline.py`) 및 세션 캐시 관리 비즈니스 로직을 다룹니다.
2. **격리 규칙:** 
   - 현재 디렉토리가 `.agents/worktrees/arti_core` 인지 확인하고 격리된 폴더 내부에서만 활동하십시오.
   - 단위 개발 완료 후 `.agents/scripts/ralph-loop.sh arti_core <티켓명>`을 통해 TDD 테스트를 수행하십시오.
