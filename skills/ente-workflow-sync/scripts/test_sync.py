#!/usr/bin/env python3
"""Acceptance tests: real Git repositories, no external network or credentials."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).with_name("sync.py")
IGNORE = "*\n!/.gitignore\n!/tasks/\n!/tasks/**\n!/skills/\n!/skills/**\n"


class SyncAcceptance(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name).resolve()
        self.origin = self.base / "origin.git"
        self.git(self.base, "init", "--bare", "--initial-branch=main", str(self.origin))
        self.air = self.clone("air", "macbook-air")
        self.write(self.air, ".gitignore", IGNORE)
        self.write(self.air, "tasks/shared/PRD.md", "Original plan.\n")
        self.git(self.air, "add", ".")
        self.git(self.air, "commit", "-m", "Initial workflow")
        self.git(self.air, "push", "origin", "HEAD:main")
        self.mini = self.clone("mini", "mac-mini")

    def git(self, root, *args, check=True):
        result = subprocess.run(["git", "-C", str(root), *args], text=True,
                                capture_output=True, timeout=20,
                                env={**os.environ, "GIT_TERMINAL_PROMPT": "0"})
        if check:
            self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.strip()

    def clone(self, name, machine):
        root = self.base / name
        self.git(self.base, "clone", str(self.origin), str(root))
        self.git(root, "config", "user.name", "Workflow Test")
        self.git(root, "config", "user.email", "workflow@example.test")
        self.write(root, ".workflow/local.json", json.dumps({
            "machine": machine, "expected_remote": str(self.origin),
            "skill_roots": [str(self.base / (name + "-codex")),
                            str(self.base / (name + "-claude"))],
        }))
        return root

    def write(self, root, name, contents):
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contents)
        return path

    def run_sync(self, root, command="sync", ok=True, env=None):
        result = subprocess.run([sys.executable, str(SCRIPT), "--root", str(root), command],
                                text=True, capture_output=True, timeout=30,
                                env={**os.environ, **(env or {})})
        if ok:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "ok" if ok else payload["status"])
        self.assertEqual(payload, json.loads((root / ".workflow/sync-status.json").read_text()))
        return payload

    def test_removed_skill_unlinks_but_preserves_ignored_local_cache(self):
        self.write(self.air, '.gitignore', IGNORE + '**/__pycache__/\n')
        self.write(self.air, 'skills/example/SKILL.md', 'Example skill\n')
        self.run_sync(self.air)
        self.run_sync(self.mini)
        cache = self.write(self.mini, 'skills/example/__pycache__/local.pyc', 'Local cache')
        (self.air / 'skills/example/SKILL.md').unlink()
        self.run_sync(self.air)
        self.run_sync(self.mini)
        self.assertEqual(cache.read_text(), 'Local cache')
        for app in ('codex', 'claude'):
            self.assertFalse((self.base / ('mini-' + app) / 'example').is_symlink())

    def test_concurrent_nonconflicting_edits_survive_retries(self):
        self.write(self.air, "tasks/air/PRD.md", "Air decision\n")
        self.write(self.mini, "tasks/mini/PRD.md", "Mini decision\n")
        self.run_sync(self.air)
        self.run_sync(self.mini)
        self.run_sync(self.air)
        for root in (self.air, self.mini):
            self.assertEqual((root / "tasks/air/PRD.md").read_text(), "Air decision\n")
            self.assertEqual((root / "tasks/mini/PRD.md").read_text(), "Mini decision\n")
            self.assertEqual(self.git(root, "status", "--porcelain"), "")

    def test_conflicting_edits_retain_both_commits_and_stop(self):
        self.write(self.air, "tasks/shared/PRD.md", "Air choice\n")
        self.write(self.mini, "tasks/shared/PRD.md", "Mini choice\n")
        self.run_sync(self.air)
        remote_commit = self.git(self.air, "rev-parse", "HEAD")
        result = self.run_sync(self.mini, ok=False)
        self.assertEqual(result["status"], "conflict")
        self.assertEqual(self.git(self.mini, "show", "HEAD:tasks/shared/PRD.md"), "Mini choice")
        self.assertEqual(self.git(self.mini, "show", remote_commit + ":tasks/shared/PRD.md"), "Air choice")
        self.assertTrue(self.git(self.mini, "ls-files", "-u"))
        head = self.git(self.mini, "rev-parse", "HEAD")
        self.run_sync(self.mini, ok=False)
        self.assertEqual(self.git(self.mini, "rev-parse", "HEAD"), head)

    def test_offline_fetch_preserves_local_commit(self):
        self.origin.rename(self.base / "offline-origin.git")
        old = self.git(self.air, "rev-parse", "HEAD")
        self.write(self.air, "tasks/offline/PRD.md", "Offline work\n")
        result = self.run_sync(self.air, ok=False)
        self.assertEqual(result["status"], "pending")
        self.assertNotEqual(self.git(self.air, "rev-parse", "HEAD"), old)
        self.assertEqual(self.git(self.air, "show", "HEAD:tasks/offline/PRD.md"), "Offline work")

    def test_remote_advance_during_push_is_retained_and_next_sync_retries(self):
        self.write(self.air, "tasks/air/PRD.md", "Air decision\n")
        self.write(self.mini, "tasks/mini/PRD.md", "Mini decision\n")
        self.git(self.mini, "add", ".")
        self.git(self.mini, "commit", "-m", "Mini concurrent decision")
        import shlex
        hook = self.write(self.air, ".git/hooks/pre-push", "#!/bin/sh\n" +
                          "git -C " + shlex.quote(str(self.mini)) + " push origin HEAD:main\n")
        hook.chmod(0o755)
        result = self.run_sync(self.air, ok=False)
        self.assertEqual(result["status"], "pending")
        self.assertEqual(self.git(self.air, "show", "HEAD:tasks/air/PRD.md"), "Air decision")
        self.assertEqual(self.git(self.origin, "show", "main:tasks/mini/PRD.md"), "Mini decision")
        hook.unlink()
        self.run_sync(self.air)
        self.run_sync(self.mini)
        self.assertEqual((self.mini / "tasks/air/PRD.md").read_text(), "Air decision\n")
        self.assertEqual((self.air / "tasks/mini/PRD.md").read_text(), "Mini decision\n")

    def test_prestaged_changes_are_untouched(self):
        self.write(self.air, "tasks/shared/PRD.md", "Already reviewed\n")
        self.git(self.air, "add", "tasks/shared/PRD.md")
        before = self.git(self.air, "diff", "--cached")
        head = self.git(self.air, "rev-parse", "HEAD")
        self.run_sync(self.air, ok=False)
        self.assertEqual(self.git(self.air, "diff", "--cached"), before)
        self.assertEqual(self.git(self.air, "rev-parse", "HEAD"), head)

    def test_manual_branch_is_not_committed_or_published_to_main(self):
        self.git(self.air, "checkout", "-b", "manual-edit")
        self.write(self.air, "tasks/shared/PRD.md", "Unapproved branch work\n")
        head = self.git(self.air, "rev-parse", "HEAD")
        result = self.run_sync(self.air, ok=False)
        self.assertIn("main", result["error"])
        self.assertEqual(self.git(self.air, "rev-parse", "HEAD"), head)
        self.assertEqual(self.git(self.origin, "rev-parse", "main"), head)
        self.assertEqual(self.git(self.air, "diff", "--cached"), "")

    def test_detached_head_is_not_committed_or_published_to_main(self):
        self.git(self.air, "checkout", "--detach")
        self.write(self.air, "tasks/shared/PRD.md", "Detached work\n")
        head = self.git(self.air, "rev-parse", "HEAD")
        result = self.run_sync(self.air, ok=False)
        self.assertIn("main", result["error"])
        self.assertEqual(self.git(self.air, "rev-parse", "HEAD"), head)
        self.assertEqual(self.git(self.origin, "rev-parse", "main"), head)
        self.assertEqual(self.git(self.air, "diff", "--cached"), "")

    def test_index_content_is_checked_after_the_staging_boundary(self):
        wrapper = self.write(self.base, "bin/git", "#!" + sys.executable + "\n" + '''
import os
from pathlib import Path
import subprocess
import sys
args = sys.argv[1:]
actual_git = os.environ["ACTUAL_GIT"]
if len(args) > 2 and args[2] == "add":
    path = Path(os.environ["LATE_PATH"])
    mode = os.environ["LATE_MODE"]
    if mode == "symlink":
        path.unlink()
        path.symlink_to("../../../../outside")
    elif mode != "gitlink":
        content = "x" * (10 * 1024 * 1024 + 1) if mode == "large" else os.environ["LATE_CONTENT"]
        path.write_text(content)
    result = subprocess.call([actual_git, *args])
    if mode == "gitlink" and result == 0:
        result = subprocess.call([actual_git, *args[:2], "update-index", "--add", "--cacheinfo",
                                  "160000," + os.environ["LATE_COMMIT"] + ",tasks/embedded"])
    else:
        if path.is_symlink():
            path.unlink()
        path.write_text("Safe working content\\n")
    sys.exit(result)
sys.exit(subprocess.call([actual_git, *args]))
''')
        wrapper.chmod(0o755)
        for mode, relative in (("secret", "tasks/new/PRD.md"),
                               ("personal-token", "tasks/new/PRD.md"),
                               ("filename", "tasks/new/auth.json"),
                               ("large", "tasks/new/PRD.md"),
                               ("symlink", "tasks/new/link.md"),
                               ("gitlink", "tasks/embedded")):
            with self.subTest(mode=mode):
                token = ("ghp_" if mode == "personal-token" else "gho_") + "c" * 40
                root = self.clone("late-" + mode, "macbook-air")
                self.write(root, "tasks/new/PRD.md", "Safe notes\n")
                if mode == "symlink":
                    self.write(root, relative, "Safe link placeholder\n")
                head = self.git(root, "rev-parse", "HEAD")
                result = self.run_sync(root, ok=False, env={
                    "PATH": str(wrapper.parent) + os.pathsep + os.environ["PATH"],
                    "ACTUAL_GIT": shutil.which("git"), "LATE_PATH": str(root / relative),
                    "LATE_MODE": mode, "LATE_CONTENT": token, "LATE_COMMIT": head,
                })
                self.assertEqual(self.git(root, "rev-parse", "HEAD"), head,
                                 "Unchecked index content must never enter a commit")
                self.assertEqual(self.git(self.origin, "rev-parse", "main"), head)
                self.assertTrue(self.git(root, "diff", "--cached"), "Preserve the index for review")
                self.assertIn(relative, result["error"])
                self.assertNotIn(token, json.dumps(result))
                if mode in {"secret", "personal-token"}:
                    self.assertEqual(self.git(root, "show", ":" + relative), token)
                    self.assertEqual((root / relative).read_text(), "Safe working content\n")

    def test_skill_add_update_and_removal_reconcile_both_hosts(self):
        skill = self.write(self.air, "skills/example/SKILL.md", "First version\n")
        self.write(self.air, "skills/_licenses/NOTICE", "License\n")
        self.run_sync(self.air)
        self.run_sync(self.mini)
        for name in ("air", "mini"):
            for tool in ("codex", "claude"):
                links = self.base / (name + "-" + tool)
                self.assertTrue((links / "example").is_symlink())
                self.assertEqual((links / "example/SKILL.md").read_text(), "First version\n")
                self.assertTrue((links / "_licenses").is_symlink())
        skill.write_text("Updated version\n")
        self.run_sync(self.air)
        self.run_sync(self.mini)
        self.assertEqual((self.base / "mini-claude/example/SKILL.md").read_text(), "Updated version\n")
        skill.unlink()
        skill.parent.rmdir()
        self.run_sync(self.air)
        self.run_sync(self.mini)
        for name in ("air", "mini"):
            for tool in ("codex", "claude"):
                self.assertFalse((self.base / (name + "-" + tool) / "example").is_symlink())
                self.assertTrue((self.base / (name + "-" + tool) / "_licenses").is_symlink())

    def test_link_collisions_preserve_foreign_content(self):
        self.write(self.air, "skills/example/SKILL.md", "Shared skill\n")
        foreign = self.base / "air-codex/example"
        foreign.mkdir(parents=True)
        (foreign / "mine.txt").write_text("Keep mine")
        self.run_sync(self.air, "links", ok=False)
        self.assertEqual((foreign / "mine.txt").read_text(), "Keep mine")
        (foreign / "mine.txt").unlink()
        foreign.rmdir()
        target = self.base / "foreign-skill"
        target.mkdir()
        foreign.symlink_to(target, target_is_directory=True)
        self.run_sync(self.air, "links", ok=False)
        self.assertEqual(foreign.resolve(), target)

    def test_obsolete_foreign_symlink_is_never_removed(self):
        links = self.base / "air-codex"
        links.mkdir()
        foreign = links / "foreign"
        foreign.symlink_to(self.base / "missing-foreign", target_is_directory=True)
        self.run_sync(self.air, "links")
        self.assertTrue(foreign.is_symlink())

    def test_credentials_block_before_commit_without_echoing_secret(self):
        head = self.git(self.air, "rev-parse", "HEAD")
        token = "gho_" + "a" * 40
        self.write(self.air, "tasks/new/PRD.md", token + "\n")
        result = self.run_sync(self.air, ok=False)
        self.assertNotIn(token, json.dumps(result))
        self.assertEqual(self.git(self.air, "rev-parse", "HEAD"), head)
        self.assertEqual(self.git(self.air, "diff", "--cached"), "")

    def test_credential_filename_blocks_before_commit(self):
        self.write(self.air, "skills/example/.env.local", "SECRET=something\n")
        self.run_sync(self.air, ok=False)
        self.assertEqual(self.git(self.air, "diff", "--cached"), "")

    def test_ignored_local_config_and_logs_never_staged(self):
        self.write(self.air, "raw.log", "gho_" + "b" * 40)
        self.write(self.air, "tasks/clean/PRD.md", "Safe notes\n")
        config = (self.air / ".workflow/local.json").read_bytes()
        self.run_sync(self.air)
        tracked = self.git(self.air, "ls-files").splitlines()
        self.assertNotIn("raw.log", tracked)
        self.assertFalse(any(name.startswith(".workflow/") for name in tracked))
        self.assertEqual((self.air / ".workflow/local.json").read_bytes(), config)
        self.assertTrue((self.air / "raw.log").exists())

    def test_push_remote_mismatch_is_refused(self):
        self.git(self.air, "remote", "set-url", "--push", "origin", str(self.base / "wrong.git"))
        self.write(self.air, "tasks/new/PRD.md", "Safe notes\n")
        self.run_sync(self.air, ok=False)
        self.assertEqual(self.git(self.air, "diff", "--cached"), "")

    def test_fetch_remote_mismatch_is_refused(self):
        self.git(self.air, "remote", "set-url", "origin", str(self.base / "wrong.git"))
        self.run_sync(self.air, ok=False)

    def test_wrong_root_is_refused(self):
        nested = self.air / "tasks"
        self.write(nested, ".workflow/local.json", (self.air / ".workflow/local.json").read_text())
        self.run_sync(nested, ok=False)

    def test_nested_git_and_escaping_symlink_are_refused(self):
        nested = self.air / "skills/nested"
        nested.mkdir(parents=True)
        self.git(nested, "init")
        self.run_sync(self.air, ok=False)
        # Remove the fixture-only nested repository before testing a separate condition.
        import shutil
        shutil.rmtree(nested)
        (self.air / "skills/escape").symlink_to(self.base, target_is_directory=True)
        self.run_sync(self.air, ok=False)
        self.assertTrue((self.air / "skills/escape").is_symlink())

    def test_links_work_without_git_repository(self):
        root = self.base / "notes-only"
        self.write(root, ".workflow/local.json", (self.air / ".workflow/local.json").read_text())
        self.write(root, "skills/standalone/SKILL.md", "Local skill\n")
        self.run_sync(root, "links")
        self.assertEqual((self.base / "air-codex/standalone").resolve(), root / "skills/standalone")

    def test_files_changed_by_commit_hook_stop_before_merge(self):
        hook = self.write(self.air, ".git/hooks/post-commit",
                          "#!/bin/sh\nprintf 'New unsaved work\\n' >> tasks/shared/PRD.md\n")
        hook.chmod(0o755)
        self.write(self.air, "tasks/new/PRD.md", "New committed work\n")
        self.run_sync(self.air, ok=False)
        self.assertEqual(self.git(self.air, "show", "HEAD:tasks/new/PRD.md"), "New committed work")
        self.assertIn("New unsaved work", (self.air / "tasks/shared/PRD.md").read_text())
        self.assertTrue(self.git(self.air, "diff"))
        self.assertNotEqual(self.git(self.air, "rev-parse", "HEAD"),
                            self.git(self.air, "rev-parse", "origin/main"))

    def test_view_is_regenerated_without_reacquiring_sync_lock(self):
        self.write(self.air, "skills/ente-task-queue/SKILL.md", "Task queue\n")
        self.write(self.air, "skills/ente-task-queue/scripts/queue.py",
                   "def render_view(root):\n    (root / 'TODO.md').write_text('New task view\\n')\n")
        self.run_sync(self.air)
        self.assertEqual((self.air / "TODO.md").read_text(), "New task view\n")
        self.assertNotIn("TODO.md", self.git(self.air, "ls-files").splitlines())

    def test_links_do_not_clear_existing_conflict_status(self):
        self.write(self.air, ".workflow/sync-status.json", json.dumps({
            "status": "conflict", "time": "2026-01-01T00:00:00+00:00",
            "error": "Merge needs review",
        }))
        result = self.run_sync(self.air, "links", ok=False)
        self.assertEqual(result["status"], "conflict")

    def test_oversized_file_blocks_before_staging(self):
        self.write(self.air, "tasks/new/large.md", "x" * (10 * 1024 * 1024 + 1))
        self.run_sync(self.air, ok=False)
        self.assertEqual(self.git(self.air, "diff", "--cached"), "")


if __name__ == "__main__":
    unittest.main()
