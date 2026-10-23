---
name: start-task
description: Start one new task in its own git worktree with a task note on the board, to work on it yourself in a new session. Use when the owner asks to start a single piece of work.
---

The `wb` command ships with this plugin. If `wb` is not on PATH, run `${CLAUDE_PLUGIN_ROOT}/bin/wb` instead. Repo settings are in `workbench.conf`; `wb where` prints the hub (memory/ and tasks/).

Start a task for: $ARGUMENTS

1. Read the spec and run `wb status`. If another task already covers this, say so and stop.
2. Pick a short kebab-case name and a one-line goal in the owner's words.
3. Run `wb new <name> "<goal>"`.
4. In the task note, set `next:` to the first concrete step and add a `## Plan` (3-6 bullets).
5. Tell the owner the worktree path and `cd <path> && claude`, plus the plan. For anything
   large, wait for their OK before writing code.
