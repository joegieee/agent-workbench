---
name: ship
description: Finish the current task - run the repo's checks, commit following AGENTS.md, push, open a PR, update the task note, the spec and memory. Use when the work in this worktree is done.
---

The `wb` command ships with this plugin. If `wb` is not on PATH, run `${CLAUDE_PLUGIN_ROOT}/bin/wb` instead. Repo settings are in `workbench.conf`; `wb where` prints the hub (memory/ and tasks/).

1. Run `wb check`. Fix failures; never skip or disable a test to get green.
2. Commit following AGENTS.md (author, message style, attribution rules). The commit-msg hook
   enforces `author_email` and strips AI trailers when workbench.conf asks for it.
3. Push (`git push -u origin HEAD`) and open a PR against the base branch (`gh pr create`).
   Body: what changed, why, how it was tested, results.
4. Task note: `state: review`, `pr: <url>`, `next: owner review`, plus a log line.
5. If this finishes a milestone or changes a decision, update the spec. Save durable facts to
   memory.
6. Report: the PR link, what works, test results, the next step.

After the PR merges, `wb done <task>` marks it done and removes the worktree if it's clean.
