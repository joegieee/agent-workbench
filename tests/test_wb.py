"""End-to-end tests for bin/wb against throwaway git repos. Run: python3 -m unittest -v"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

WB = Path(__file__).resolve().parent.parent / "plugins" / "wb" / "bin" / "wb"
AUTHOR = "Test Author", "author@example.com"


class WbTest(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.env = {
            **os.environ,
            "HOME": str(self.root / "home"),
            "WB_HOME": str(self.root / "hubs"),
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": str(self.root / "gitconfig"),
        }
        (self.root / "home").mkdir()
        # An "origin" with one commit on main, and a clone to work in.
        self.origin = self.root / "origin.git"
        self.git("init", "-q", "--bare", "-b", "main", str(self.origin), cwd=self.root)
        self.repo = self.root / "code" / "app"
        self.git("clone", "-q", str(self.origin), str(self.repo), cwd=self.root)
        self.git("config", "user.name", "Someone Else")
        self.git("config", "user.email", "other@example.com")
        (self.repo / ".gitignore").write_text(".env\n")
        (self.repo / ".env").write_text("SECRET=1\n")

    def git(self, *args: str, cwd: Path | None = None) -> str:
        return subprocess.run(
            ["git", *args],
            cwd=cwd or self.repo,
            env=self.env,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

    def wb(
        self, *args: str, cwd: Path | None = None, ok: bool = True
    ) -> subprocess.CompletedProcess[str]:
        proc = subprocess.run(
            [sys.executable, str(WB), *args],
            cwd=cwd or self.repo,
            env=self.env,
            capture_output=True,
            text=True,
            check=False,
        )
        if ok:
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        return proc

    def init_repo(self, *extra: str) -> None:
        self.wb(
            "init",
            "--name",
            "app",
            "--check",
            "true",
            "--author-name",
            AUTHOR[0],
            "--author-email",
            AUTHOR[1],
            *extra,
        )
        self.git("add", "-A")
        self.git("-c", f"user.email={AUTHOR[1]}", "commit", "-q", "-m", "Add workbench")
        self.git("push", "-q", "origin", "main")
        self.wb("setup")

    @property
    def hub(self) -> Path:
        return self.root / "hubs" / "app"

    def test_init_writes_config_and_agent_files(self) -> None:
        self.wb(
            "init",
            "--name",
            "app",
            "--spec-url",
            "https://example.com/spec",
            "--author-email",
            AUTHOR[1],
        )
        conf = (self.repo / "workbench.conf").read_text()
        self.assertIn("name=app", conf)
        self.assertIn("spec_url=https://example.com/spec", conf)
        self.assertTrue((self.repo / "AGENTS.md").is_file())
        self.assertIn("@~/.workbench/app/memory/MEMORY.md", (self.repo / "CLAUDE.md").read_text())
        settings = json.loads((self.repo / ".claude" / "settings.json").read_text())
        self.assertEqual(settings["attribution"], {"commit": "", "pr": ""})
        # Re-running keeps an existing config.
        (self.repo / "workbench.conf").write_text("name=custom\n")
        self.wb("init")
        self.assertEqual((self.repo / "workbench.conf").read_text(), "name=custom\n")

    def test_commands_need_a_config(self) -> None:
        proc = self.wb("status", ok=False)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("wb init", proc.stderr)

    def test_setup_creates_hub_identity_and_hook(self) -> None:
        self.init_repo()
        self.assertTrue((self.hub / "memory" / "MEMORY.md").is_file())
        self.assertTrue((self.hub / "tasks").is_dir())
        self.assertEqual(self.git("config", "user.email"), AUTHOR[1])
        self.assertIn("hook commit-msg", (self.repo / ".git" / "hooks" / "commit-msg").read_text())

    def test_new_task_makes_worktree_note_and_links_shared_files(self) -> None:
        self.init_repo()
        out = self.wb("new", "search-api", "Add a search endpoint").stdout
        wt = self.root / "code" / "app.worktrees" / "search-api"
        self.assertIn(str(wt), out)
        self.assertEqual(self.git("branch", "--show-current", cwd=wt), "task/search-api")
        self.assertTrue((wt / ".env").is_symlink())
        note = (self.hub / "tasks" / "search-api.md").read_text()
        self.assertIn("goal: Add a search endpoint", note)
        self.assertIn("state: working", note)
        self.assertEqual(self.wb("new", "Bad Name", "x", ok=False).returncode, 1)
        self.assertEqual(self.wb("new", "search-api", "again", ok=False).returncode, 1)

    def test_status_board_shows_state_dirty_question_and_quota(self) -> None:
        ledger = self.root / "ledger.json"
        today = datetime.now(ZoneInfo("America/Los_Angeles")).date().isoformat()
        ledger.write_text(json.dumps({"gemini": {today: 7}}))
        self.init_repo()
        conf = self.repo / "workbench.conf"
        conf.write_text(
            conf.read_text()
            .replace("quota_ledger=\n", f"quota_ledger={ledger}\n")
            .replace("quota_tz=UTC", "quota_tz=America/Los_Angeles")
        )
        self.wb("new", "one", "First")
        self.wb("new", "two", "Second")
        wt = self.root / "code" / "app.worktrees" / "one"
        (wt / "a.txt").write_text("x")
        note = self.hub / "tasks" / "two.md"
        note.write_text(
            note.read_text()
            .replace("state: working", "state: blocked")
            .replace("blocked-on:", "blocked-on: which database?")
        )
        board = self.wb("status").stdout
        lines = {
            line.split()[0]: line.split() for line in board.splitlines() if line and line[0] != " "
        }
        self.assertEqual(lines["one"][1:3], ["working", "1"])
        self.assertEqual(lines["two"][1], "blocked")
        self.assertIn("question: which database?", board)
        self.assertIn("gemini 7", board)
        self.assertNotIn("question:", self.wb("status", "--brief").stdout)

    def test_status_survives_a_deleted_worktree_folder(self) -> None:
        self.init_repo()
        self.wb("new", "gone", "Gone")
        self.wb("new", "kept", "Kept")
        wt = self.root / "code" / "app.worktrees" / "gone"
        shutil.rmtree(wt)
        board = self.wb("status", "--brief").stdout
        self.assertIn(f"missing worktree: {wt}", board)
        self.assertIn("kept", board)

    def test_commit_hook_strips_ai_trailers_and_checks_author(self) -> None:
        self.init_repo()
        self.wb("new", "fix", "Fix it")
        wt = self.root / "code" / "app.worktrees" / "fix"
        (wt / "f.txt").write_text("x")
        self.git("add", "f.txt", cwd=wt)
        msg = (
            "Fix it\n\nCo-Authored-By: Claude <noreply@anthropic.com>\n"
            "Claude-Session: https://claude.ai/x\nReviewed-by: A Person <a@example.com>\n"
        )
        self.git("commit", "-q", "-m", msg, cwd=wt)
        body = self.git("log", "-1", "--format=%B", cwd=wt)
        self.assertNotIn("Claude", body)
        self.assertIn("Reviewed-by: A Person", body)
        self.assertEqual(self.git("log", "-1", "--format=%ae", cwd=wt), AUTHOR[1])
        proc = subprocess.run(
            [
                "git",
                "-c",
                "user.email=wrong@example.com",
                "commit",
                "-q",
                "--allow-empty",
                "-m",
                "x",
            ],
            cwd=wt,
            env=self.env,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("expected author@example.com", proc.stderr)

    def test_commit_hook_falls_back_when_its_wb_is_gone(self) -> None:
        # setup run from a copy of the plugin (like a versioned plugin cache) that later goes away
        copy = self.root / "plugin-copy"
        shutil.copytree(WB.parent.parent, copy)
        self.init_repo()
        subprocess.run(
            [sys.executable, str(copy / "bin" / "wb"), "setup"],
            cwd=self.repo,
            env=self.env,
            check=True,
            capture_output=True,
        )
        shutil.rmtree(copy)
        env = {**self.env, "PATH": ""}
        bad = ["git", "-c", "user.email=wrong@example.com", "commit", "--allow-empty", "-m", "x"]
        # No wb anywhere: the commit goes through with a warning.
        proc = subprocess.run(
            ["/usr/bin/env", f"PATH={os.defpath}", *bad],
            cwd=self.repo,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("wb not found", proc.stderr)
        # wb on PATH: the hook uses it and enforces the author again.
        bindir = self.root / "bin"
        bindir.mkdir()
        (bindir / "wb").symlink_to(WB)
        proc = subprocess.run(
            ["/usr/bin/env", f"PATH={bindir}{os.pathsep}{os.defpath}", *bad],
            cwd=self.repo,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("expected author@example.com", proc.stderr)

    def test_dispatch_validates_brief_and_recreates_missing_note(self) -> None:
        self.init_repo()
        bindir = self.root / "bin"
        bindir.mkdir()
        fake = bindir / "claude"
        fake.write_text(f'#!/bin/sh\necho "$@" > "{self.root}/claude-args"\n')
        fake.chmod(0o755)
        self.env["PATH"] = f"{bindir}{os.pathsep}{self.env['PATH']}"
        proc = self.wb("dispatch", "empty", "  ", ok=False)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("brief is empty", proc.stderr)
        self.assertNotIn("Traceback", proc.stderr)

        self.wb("new", "orphan", "Orphan")
        note = self.hub / "tasks" / "orphan.md"
        note.unlink()
        self.wb("dispatch", "orphan", "Do the thing\nin detail")
        text = note.read_text()
        self.assertIn("goal: Do the thing", text)
        self.assertIn("branch: task/orphan", text)
        self.assertIn("session: ", text)
        self.assertIn("--name orphan", (self.root / "claude-args").read_text())

    def test_done_removes_clean_worktree_only(self) -> None:
        self.init_repo()
        self.wb("new", "a", "A")
        self.wb("new", "b", "B")
        wt_b = self.root / "code" / "app.worktrees" / "b"
        (wt_b / "dirty.txt").write_text("x")
        self.wb("done", "a")
        self.assertFalse((self.root / "code" / "app.worktrees" / "a").exists())
        self.assertIn("state: done", (self.hub / "tasks" / "a.md").read_text())
        self.assertEqual(self.wb("done", "b", ok=False).returncode, 1)
        self.assertTrue(wt_b.exists())
        self.assertIn("state: working", (self.hub / "tasks" / "b.md").read_text())

    def test_check_runs_configured_command(self) -> None:
        self.init_repo()
        self.wb("check")
        conf = self.repo / "workbench.conf"
        conf.write_text(conf.read_text().replace("check=true", "check=false"))
        self.assertEqual(self.wb("check", ok=False).returncode, 1)

    def test_where_prints_hub(self) -> None:
        self.init_repo()
        self.assertEqual(self.wb("where").stdout.strip(), str(self.hub))


if __name__ == "__main__":
    unittest.main()
