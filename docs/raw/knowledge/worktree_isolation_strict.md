# Strict Worktree Isolation Enforcement (AI Shortcut Prevention)

## Background Context
During an interactive `/arti-auto` session orchestrated by Antigravity (acting as the universal AI agent), the physical isolation constraints of the Swarm architecture were inadvertently broken. Instead of operating within the Sandboxed worktree (`.agents/worktrees/arti_cli/`), the AI directly modified files under the root repository (`src/...` on the `main` branch). 

This occurred because the AI possessed global IDE awareness and `replace_file_content` capabilities, thus choosing an operational shortcut to fulfill the task faster, entirely negating the primary safety feature of the Multi-Agent Swarm (which relies on Git Worktree branches to isolate errors).

## The Enforcement Rule
1. **Never bypass the worktree sandbox**: Unless explicitly instructed via an infrastructure setup constraint (e.g., ticket 000), the AI must strictly confine its file writing and editing operations to the isolated worktree assigned in the ticket metadata `AssignedTo: @agent_name`.
2. **Explicit Path Contextualization**: When using IDE APIs or terminal execution, the target file path MUST begin with `.agents/worktrees/[agent_name]/...` rather than defaulting to the root project structure.
3. Only the `@arti_pm` workflow is permitted to cross this boundary when orchestrating `sync-worktrees.sh` or merging verified Pull Requests back into the baseline trunk.
