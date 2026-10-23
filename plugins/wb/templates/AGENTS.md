# AGENTS.md

Instructions for AI coding agents working on this repo. They are tool-neutral: Claude Code
reads them through CLAUDE.md, and Codex, Cursor and Gemini CLI read this file directly.

## The project

<!-- One paragraph: what it is, who it's for, the quality bar. -->

## Start of every session

1. Read the spec (`spec_url` in `workbench.conf`). It is the source of truth.
2. Read the memory index: `$(wb where)/memory/MEMORY.md`.
3. Run `wb status` to see the other tasks in flight. Don't start work another task owns.

## Commands

<!-- install, run, test, lint. Keep `check=` in workbench.conf equal to what CI runs. -->

## Conventions

<!-- code style, commit rules, what must never happen. -->

## Coordinator and workers

The owner usually runs one *coordinator* session in the main checkout. It plans, splits work
into tasks and hands each to a *worker*: a background session in the task's own worktree
(`wb dispatch`). If you are a worker, your prompt names your task and task note: stay in your
worktree, keep the note current, and when you need the owner set `state: blocked` with the
question and wait. Never dispatch workers unless you are the coordinator and the owner
approved the task list.

## Task notes

`$(wb where)/tasks/<task>.md` is how the owner and other agents see your work. Keep
`state:` (working | blocked | review | done), `next:`, `blocked-on:` and `pr:` current, and
add a dated line under `## Log` for anything a later session would need.

## Memory

`$(wb where)/memory/` is shared by every worktree on this machine: one file per subject,
indexed in `MEMORY.md`. Save a fact in the session you learn it if a later session would
otherwise have to ask the owner again. No secrets. The spec wins over memory: when a
decision changes the spec, update the spec first.

## Finishing a task

1. `wb check` passes.
2. Commit, push the branch, open a PR.
3. Task note: `state: review`, the PR link.
4. Update the spec if a milestone or decision changed; save durable facts to memory.
