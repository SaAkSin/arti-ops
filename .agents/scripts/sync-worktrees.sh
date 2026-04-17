#!/bin/bash
DEFAULT_BRANCH=$(git branch --show-current || git rev-parse --abbrev-ref HEAD)
ROOT_DIR=$(pwd)

for dir in .agents/worktrees/*; do
  if [ -d "$dir" ]; then
    echo "Syncing $DEFAULT_BRANCH to $dir..."
    (cd "$dir" && git merge $DEFAULT_BRANCH -m "chore: sync legacy codebase" --no-edit || (git merge --abort && echo "Conflict in $dir" >> "$ROOT_DIR/.agents/tmp/conflict.log"))
  fi
done

# 마스터 베이스라인이 갱신되었으므로 지식 그래프 최신화 (캐시 기반 0.1초 고속 갱신)
echo "Updating Global Knowledge Graph..."
(cd "$ROOT_DIR" && graphify update ./ || true)
