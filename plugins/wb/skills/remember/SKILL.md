---
name: remember
description: Save a durable fact or decision to the repo's shared local memory (and to the spec when it changes scope or decisions). Use when the owner says "remember ..." or a decision is made that later sessions need.
---

The `wb` command ships with this plugin. If `wb` is not on PATH, run `${CLAUDE_PLUGIN_ROOT}/bin/wb` instead. Repo settings are in `workbench.conf`; `wb where` prints the hub (memory/ and tasks/).

Save: $ARGUMENTS

1. Memory is `$(wb where)/memory/`: one file per subject, indexed one line per file in
   `MEMORY.md`. Update the file that covers the subject; create one only for a new subject
   and add it to the index.
2. Write the fact with its date (YYYY-MM-DD); for a decision add a **Why:** line. Replace stale
   lines instead of appending contradictions.
3. Never store secrets. Don't store what git or the code already records.
4. If it changes scope, a milestone or a recorded decision, update the spec too (following any
   rules AGENTS.md gives for it). The spec is the source of truth.
5. Confirm in one line what you saved and where.
