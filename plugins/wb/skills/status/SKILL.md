---
name: status
description: Show the task board (all worktrees, their state, PRs, next steps, open questions) and say what needs the owner. Use when asked "status", "what's going on", or "what needs me".
---

The `wb` command ships with this plugin. If `wb` is not on PATH, run `${CLAUDE_PLUGIN_ROOT}/bin/wb` instead. Repo settings are in `workbench.conf`; `wb where` prints the hub (memory/ and tasks/).

1. Run `wb status` and `claude agents --json` (skip the latter if it fails).
2. Reply in a few lines: what needs the owner first (blocked tasks with their question, workers
   waiting on a permission prompt, PRs to review, with links), then what's in progress, then
   the quota line if the board shows one. Don't paste the raw table unless asked.
3. Flag stale tasks (no log line in 3+ days while `working`) and notes without a worktree.
