# Troubleshoot 006: CLI Argument Deprecation and Environment PATH Failures

## Context & Phenomenon
Following the integration of the automatic background Graphify execution inside `sync-worktrees.sh`, users experienced two adjacent errors:
1. `error: unknown command '--update'`
2. `graphify: command not found`

These command outputs interrupted or polluted the terminal view immediately following the conclusion of ticket merge actions.

## Root Cause Analysis
1. **API/CLI Syntax Deprecation**: The Graphify ecosystem updated its CLI handling mechanics natively abandoning the `--update` parameter in favor of the Positional + Command structure, namely `update <path>`. Consequently, invoking `graphify --update` forcefully threw a usage violation exception and exited.
2. **Bash Sub-Shell Environment Sourcing**: The command was structured simply as `graphify` inside a pure `/bin/bash` script runner. Due to the differences between interactive shell configurations (like `.zshrc` defining `/opt/homebrew/.../bin` in PATH) and non-interactive shell initializations, the binary alias was unrecognized.

## Resolution (Applied Solutions)
1. Performed a full repository-wide text transition replacing deprecated instances (`graphify --update`) with `graphify update ./`. Target areas included background executing bash scripts and `global_workflows` static references uniformly.
2. Reasserted the fail-safe (`|| true`) handling pattern within `.agents/scripts/sync-worktrees.sh` allowing graceful skips if user environments severely misallocate tools, thereby securing core pipeline execution.

## Architectural Takeaway
Whenever leveraging external third-party software executables (like `graphify` or `uv`) from within internal bash scripts spanning numerous autonomous agents:
- Do NOT assume immutable API parameter flags over time; be swift to apply unified search/replace operations across `global_workflows`.
- NEVER permit a failure of a secondary extraction/update task to panic or break the overarching primary pipeline logic structure if it can just execute `|| true` as a temporary silent failure.
