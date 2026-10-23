# agent-workbench

A Claude Code plugin for running several coding agents on one repo at once, on your own machine.
Each task gets its own git worktree and branch. A coordinator session plans the work and hands
tasks to background workers. A task board shows what each one is doing, and memory is shared
across all of them.

Nothing runs on a schedule: every command runs only when you or an agent calls it.

```
you ── /wb:coordinate ──► coordinator session (main checkout)
                              │  wb dispatch <task> "<brief>"
                              ▼
          worker: claude --bg in ../<repo>.worktrees/<task>   (one per task)
                              │  keeps ~/.workbench/<repo>/tasks/<task>.md current
                              ▼
                      wb status / /wb:status  ◄── what's running, blocked, in review
```

## What's in it

| Piece | What it does |
|---|---|
| `wb` CLI (`plugins/wb/bin/wb`, Python 3.10+, no dependencies) | `init`, `setup`, `new`, `dispatch`, `status`, `check`, `done`, `where`, `hook` |
| Skills | `/wb:coordinate`, `/wb:start-task`, `/wb:status`, `/wb:remember`, `/wb:ship` |
| SessionStart hook | In repos with a `workbench.conf`, prints the task board (read-only, no network) when a session opens |
| commit-msg hook | Installed by `wb setup`: strips `Co-Authored-By: <AI>` / `Claude-Session:` lines and enforces the configured author email |
| `templates/AGENTS.md` | A tool-neutral starting point for a repo's agent instructions |

Per machine, each repo gets a hub at `~/.workbench/<name>/`:

```
memory/MEMORY.md     index of memory files (one file per subject next to it)
tasks/<task>.md      state / next / blocked-on / pr, plus a dated log
```

## Install (once per machine)

Requires git, Python 3.10+ and Claude Code with background sessions (`claude update`).
The GitHub CLI (`gh`) is optional: it lets workers open PRs and the board show PR state.

```bash
git clone https://github.com/joegieee/agent-workbench.git ~/code/agent-workbench
claude plugin marketplace add ~/code/agent-workbench
claude plugin install wb@agent-workbench
ln -s ~/code/agent-workbench/plugins/wb/bin/wb ~/.local/bin/wb   # `wb` in your own terminal
```

Update later with `git -C ~/code/agent-workbench pull` and
`claude plugin marketplace update agent-workbench`.

## Add a repo (once per repo)

```bash
cd ~/code/my-app
wb init --spec-url https://... --check "npm test" \
        --author-name "Jewel" --author-email "you@users.noreply.github.com"
# review workbench.conf, AGENTS.md and CLAUDE.md, then commit them
wb setup        # per machine: hub, memory index, git identity, commit-msg hook
```

`workbench.conf` is plain `key=value`. The keys:

| Key | Meaning |
|---|---|
| `name` | hub folder: `~/.workbench/<name>` |
| `github_repo` | `owner/repo`, for PR state on the board |
| `spec_url` | where the source of truth lives (Notion, a doc...) |
| `base_branch` | branch new tasks start from (default `main`) |
| `check` | what must pass before a commit; `wb check` runs it |
| `shared_files` | gitignored files linked into every worktree (default `.env`) |
| `setup_cmd` | run once per machine by `wb setup` (`$WB_HUB` = hub path) |
| `worktree_cmd` | run in each new worktree, e.g. `uv sync` or `npm ci` |
| `author_name`, `author_email` | commit identity for this repo; the hook enforces the email |
| `strip_ai_trailers` | `true` removes AI co-author/session lines from commit messages |
| `quota_ledger`, `quota_tz` | optional JSON `{provider: {YYYY-MM-DD: n}}` shown on the board, e.g. a daily LLM request count (`{hub}` and `~` expand) |

## Daily use

```bash
cd ~/code/my-app && claude
> /wb:coordinate add search to the API and fix the flaky login test
```

The coordinator reads the spec and the board, proposes tasks, and after your OK runs
`wb dispatch <task> "<brief>"` for each. Then:

- `claude agents` lists the workers: running, waiting on you, or finished.
- `claude attach <task>` opens one to answer a question or approve a command.
- Workers keep the repo's normal permissions, so anything outside your allowlist (push, PR,
  network) waits for your approval.
- A finished worker runs `/wb:ship`: checks, commit, push, PR, note set to `review`.
- After a merge, `wb done <task>` marks it done and removes the worktree if it's clean.

To work on a task yourself: `wb new <task> "<goal>"`, then `cd` into the worktree and run
`claude`. `wb status` shows the board from any terminal.

Example board:

```
TASK              STATE     DIRTY  PR         NEXT
main              -         0      -
mcp-server        blocked   0      -          wait for owner
                                                question: expose ask() or only the tools?
readme-results    review    0      #12 open   owner review of PR
retrieval-hybrid  working   3      -          add LanceDB index and vector baseline eval

Quota used on 2026-10-23 (America/Los_Angeles): gemini 7
```

## Development

```bash
python3 -m unittest discover -s tests -v    # end-to-end tests against throwaway git repos
uvx ruff check && uvx ruff format --check
claude plugin validate plugins/wb
```
