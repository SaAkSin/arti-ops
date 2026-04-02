#!/bin/bash
# setup-swarm-adapter.sh
# 비파괴형 스웜 구조 주입 (Non-Destructive Swarm Injection)

echo "▶ 1. 스웜 보드 및 워크트리 폴더 생성..."
mkdir -p .agents/board/{1-backlog,2-in_progress,3-review,4-testing,5-pending_approval,6-done,7-failed}
mkdir -p .agents/worktrees .agents/scripts .agents/skills .agents/tmp docker/mysql_swarm

echo "▶ 2. .gitignore 업데이트 (Swarm 임시 파일 무시)..."
# 중복 추가 방지
if ! grep -q "# Swarm Factory" .gitignore; then
  echo -e "\n# Swarm Factory\n.agents/worktrees/\n.agents/tmp/" >> .gitignore
fi

echo "▶ 3. 핵심 보존 커밋 (Baseline Freeze)..."
git add docs/ .agents/ setup-swarm-adapter.sh .gitignore
git commit -m "chore: inject swarm infrastructure" || true

echo "▶ 4. 기능별 에이전트 워크트리(Worktree) 분기..."
AGENTS=("arti_cli" "arti_core" "arti_tool")

for agent in "${AGENTS[@]}"; do
    echo " > $agent 워크트리 생성 중..."
    git worktree add .agents/worktrees/$agent -b feat-$agent || true
done

echo "✅ Swarm Adapter 셋업 완료!"
