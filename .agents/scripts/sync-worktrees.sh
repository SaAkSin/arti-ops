#!/bin/bash
# sync-worktrees.sh
# 기존 코드 베이스(main 브랜치)의 변경사항을 각 에이전트 워크트리로 안전하게 병합

WORKTREES_DIR=".agents/worktrees"

if [ ! -d "$WORKTREES_DIR" ]; then
    echo "워크트리 디렉토리가 존재하지 않습니다."
    exit 1
fi

for dir in "$WORKTREES_DIR"/*/; do
    if [ -d "$dir" ]; then
        agent_name=$(basename "$dir")
        echo "▶ Syncing [$agent_name] with main branch..."
        (cd "$dir" && git merge main -m "chore: sync legacy codebase" --no-edit || git merge --abort)
        echo "✅ [$agent_name] sync complete."
    fi
done
