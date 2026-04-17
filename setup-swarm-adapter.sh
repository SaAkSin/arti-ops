#!/bin/bash

# Swarm Adapter Initialization Script
# Non-Destructive: Do not delete existing files or initialize git again.

echo "Setting up Swarm Directory Structure..."
mkdir -p .agents/board/{1-backlog,2-in_progress,3-review,4-testing,5-pending_approval,6-done,7-failed} \
         .agents/worktrees \
         .agents/scripts \
         .agents/skills \
         .agents/tmp \
         docker/mysql_swarm \
         .agents/raw/knowledge \
         .agents/raw/troubleshooting \
         .agents/raw/design \
         .agents/raw/architecture

echo "Installing Graphify Engine..."
pip install graphifyy
graphify antigravity install

echo "Adding Swarm paths to .gitignore..."
if ! grep -q ".agents/worktrees/" .gitignore; then
  echo -e "\n# Swarm Factory & Graphify\n.agents/worktrees/\n.agents/tmp/\n.agents/raw/\n.graphify/" >> .gitignore
fi

echo "Preserving State..."
git add docs/ .agents/ .gitignore
git commit -m "chore: inject swarm infrastructure and graphify" || true

echo "Initializing Agent Worktrees..."
for AGENT in arti_core arti_cli arti_agent; do
    echo "Creating worktree for $AGENT..."
    git worktree add .agents/worktrees/$AGENT -b feat-$AGENT || echo "Worktree for $AGENT may already exist."
done

echo "Swarm environment setup complete!"
