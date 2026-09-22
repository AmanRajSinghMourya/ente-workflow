#!/usr/bin/env python3
"""Replay cleanup decisions against disposable repositories; never contact GitHub."""

import copy
from contextlib import redirect_stdout
from datetime import datetime, timedelta, timezone
import hashlib
from io import StringIO
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
import cleanup_guard


class CleanupReplay(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="cleanup-replay-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.repo, self.records = self.root / "repo", self.root / "records"
        self.repo.mkdir()
        self.git(self.repo, "init", "-q", "-b", "main")
        self.git(self.repo, "config", "user.name", "Fixture")
        self.git(self.repo, "config", "user.email", "fixture@example.invalid")
        (self.repo / "seed").write_text("original\n")
        self.git(self.repo, "add", "seed")
        self.git(self.repo, "commit", "-qm", "fixture")
        self.head = self.git(self.repo, "rev-parse", "HEAD").strip()
        self.wt = self.repo / ".worktrees" / "B-fixture"
        self.git(self.repo, "worktree", "add", "-q", "-b", "aman/fixture", str(self.wt))
        (self.repo / ".git/info/exclude").write_text("/.worktrees/\n/.task\n")
        self.archive = self.records / "tasks/B-fixture"
        (self.archive / "reviews").mkdir(parents=True)
        for name in ("PRD.md", "BOARD.md", "reviews/codex.md"):
            (self.archive / name).write_text("Reviewed fixture\n")
        self.git(self.repo, "bundle", "create", str(self.archive / "head.bundle"), "refs/heads/aman/fixture")
        (self.wt / ".task").symlink_to(self.archive, target_is_directory=True)
        self.now = datetime(2026, 9, 21, 12, tzinfo=timezone.utc)
        self.control = {"not_before": "2026-09-20T00:00:00Z", "cleanup_mode": "audit"}
        self.task = {"id": "B-fixture", "worktree": str(self.wt), "branch": "aman/fixture",
                     "head_sha": self.head, "status": "completed", "thread_ids": ["thread1"],
                     "depends_on": [], "prs": [], "mapping_evidence": "https://github.com/ente-io/ente/pull/20",
                     "archive": {"path": str(self.archive), "files": []}}
        self.responses = {"user": {"login": "AmanRajSinghMourya"}}
        for label, repo, number in (("fork", "AmanRajSinghMourya/ente", 10), ("upstream", "ente-io/ente", 20)):
            mapping = {"repo": repo, "number": number, "head_repo": "AmanRajSinghMourya/ente",
                       "head_branch": "aman/fixture", "head_sha": self.head, "base": "main"}
            self.task[label] = mapping
            self.task["prs"].append({"repo": repo, "number": number})
            self.responses[f"repos/{repo}/pulls/{number}"] = {
                "number": number, "state": "closed" if label == "upstream" else "open",
                "merged": label == "upstream", "merged_at": "2026-09-21T10:00:00Z" if label == "upstream" else None,
                "user": {"login": "AmanRajSinghMourya"},
                "base": {"ref": "main", "repo": {"full_name": repo}},
                "head": {"ref": "aman/fixture", "sha": self.head, "repo": {"full_name": "AmanRajSinghMourya/ente"}}}
        self.activity = {"source": "codex-app", "captured_at": self.now.isoformat(), "complete": True,
                         "threads": [{"id": "thread1", "worktree": str(self.wt), "status": "idle"}]}
        self.tasks = [self.task]
        self.refresh_manifest()

    def git(self, repo, *args):
        return subprocess.run(["git", "-C", str(repo), "-c", "core.hooksPath=/dev/null", "-c", "commit.gpgsign=false", *args], check=True, capture_output=True, text=True).stdout

    def refresh_manifest(self):
        self.task["archive"]["files"] = [{"path": str(p.relative_to(self.archive)), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
                                         for p in sorted(self.archive.rglob("*")) if p.is_file()]

    def write_records(self):
        (self.records / "control.json").write_text(json.dumps(self.control))
        (self.records / "tracked-prs.json").write_text(json.dumps({"version": 1, "tasks": self.tasks}))

    def run_audit(self, api=None):
        self.write_records()
        return cleanup_guard.audit(self.repo, self.records, self.activity, api or (lambda endpoint: copy.deepcopy(self.responses[endpoint])), self.now)

    def status(self, expected, api=None):
        result = self.run_audit(api)
        self.assertEqual(result["tasks"][0]["status"], expected, result)
        return result["tasks"][0]

    def test_valid_minimal_audit_is_non_mutating(self):
        self.assertEqual(self.git(self.wt, "check-ignore", ".task"), ".task\n")
        self.assertEqual(self.git(self.wt, "status", "--porcelain=v1", "-z", "--untracked-files=all", "--ignored=traditional"), "!! .task\0")
        before = self.git(self.repo, "worktree", "list", "--porcelain")
        result = self.status("eligible")
        self.assertEqual(len(result["proposed_actions"]), 3)
        self.assertEqual(before, self.git(self.repo, "worktree", "list", "--porcelain"))
        self.assertTrue(self.wt.exists())
        self.assertFalse(result["mutation_authorized"])

    def test_untracked_archive_directory_symlink_remains_eligible(self):
        (self.repo / ".git/info/exclude").write_text("/.worktrees/\n")
        self.assertEqual(self.git(self.wt, "status", "--porcelain=v1", "-z", "--untracked-files=all", "--ignored=traditional"), "?? .task\0")
        self.status("eligible")

    def test_activity_from_json_path_is_eligible(self):
        path = self.root / "activity.json"
        path.write_text(json.dumps(self.activity))
        self.activity = path
        result = self.run_audit()
        self.assertEqual(result["status"], "complete", result)
        self.assertEqual(result["tasks"][0]["status"], "eligible", result)

    def test_missing_or_malformed_activity_file_is_incomplete(self):
        path = self.root / "activity.json"
        self.activity = path
        for content in (None, "{broken json"):
            with self.subTest(content=content):
                if content is not None:
                    path.write_text(content)
                result = self.run_audit(lambda endpoint: self.fail("API called without readable activity evidence"))
                self.assertEqual(result["status"], "incomplete", result)
                self.assertEqual(result["tasks"], [], result)

    def test_main_activity_file_output_and_exit_codes_after_hold(self):
        self.write_records()
        path = self.root / "activity.json"
        args = ["cleanup_guard.py", "--repo", str(self.repo), "--records-root", str(self.records), "--activity-evidence", str(path)]
        for content, expected_code, expected_status in ((json.dumps(self.activity), 0, "complete"), (None, 2, "incomplete"), ("{broken json", 2, "incomplete")):
            with self.subTest(content=content):
                if content is None:
                    path.unlink()
                else:
                    path.write_text(content)
                output = StringIO()
                with patch.object(sys, "argv", args), patch.object(cleanup_guard, "github", side_effect=lambda endpoint: copy.deepcopy(self.responses[endpoint])) as api, patch.object(cleanup_guard, "datetime", wraps=datetime) as clock, redirect_stdout(output):
                    clock.now.return_value = self.now
                    code = cleanup_guard.main()
                result = json.loads(output.getvalue())
                self.assertEqual((code, result["status"]), (expected_code, expected_status), result)
                self.assertFalse(result["mutation_authorized"])
                if code == 0:
                    self.assertEqual(result["tasks"][0]["status"], "eligible", result)
                    self.assertEqual(api.call_count, 6)
                else:
                    self.assertEqual(result["tasks"], [], result)
                    api.assert_not_called()

    def test_hold_precedes_api_and_ledger_reads(self):
        self.control["not_before"] = "2026-09-23T00:00:00Z"
        self.tasks = "malformed ledger must not be read during hold"
        result = self.run_audit(lambda endpoint: self.fail("API called during hold"))
        self.assertEqual(result["status"], "held")

    def test_unmerged_upstream_blocks(self):
        pr = self.responses["repos/ente-io/ente/pulls/20"]
        pr.update(merged=False, merged_at=None)
        self.status("blocked")

    def test_wrong_author_login_pair_and_sha_are_unknown(self):
        original = copy.deepcopy(self.responses)
        changes = [("user", ("login",), "someone"),
                   ("repos/ente-io/ente/pulls/20", ("number",), 21),
                   ("repos/ente-io/ente/pulls/20", ("user", "login"), "someone"),
                   ("repos/AmanRajSinghMourya/ente/pulls/10", ("head", "sha"), "1" * 40),
                   ("repos/ente-io/ente/pulls/20", ("head", "repo", "full_name"), "other/ente")]
        for endpoint, keys, value in changes:
            with self.subTest(keys=keys, endpoint=endpoint):
                self.responses = copy.deepcopy(original)
                node = self.responses[endpoint]
                for key in keys[:-1]:
                    node = node[key]
                node[keys[-1]] = value
                self.status("unknown")

    def test_dirty_staged_untracked_ignored_files_block(self):
        (self.wt / "seed").write_text("dirty")
        self.status("blocked")
        self.git(self.wt, "add", "seed")
        self.status("blocked")
        self.git(self.wt, "reset", "--hard", "HEAD")
        (self.wt / "untracked").write_text("work")
        self.status("blocked")
        (self.wt / "untracked").unlink()
        with (self.repo / ".git/info/exclude").open("a") as handle:
            handle.write("/ignored/\n")
        (self.wt / "ignored").mkdir()
        (self.wt / "ignored/data").write_text("irreplaceable")
        self.status("blocked")

    def test_assume_unchanged_and_skip_worktree_block(self):
        for flag in ("assume-unchanged", "skip-worktree"):
            self.git(self.wt, "update-index", "--" + flag, "seed")
            self.status("blocked")
            self.git(self.wt, "update-index", "--no-" + flag, "seed")

    def test_git_operation_and_locked_worktree_block(self):
        gitdir = Path(self.git(self.wt, "rev-parse", "--absolute-git-dir").strip())
        (gitdir / "MERGE_HEAD").write_text(self.head)
        self.status("blocked")
        (gitdir / "MERGE_HEAD").unlink()
        self.git(self.repo, "worktree", "lock", str(self.wt))
        self.status("blocked")

    def test_detached_wrong_branch_and_head_block(self):
        self.git(self.wt, "checkout", "--detach", "-q")
        self.status("blocked")
        self.git(self.wt, "checkout", "-qb", "aman/other")
        self.status("blocked")

    def test_submodule_blocks(self):
        self.git(self.wt, "update-index", "--add", "--cacheinfo", "160000," + self.head + ",module")
        self.status("blocked")

    def test_shared_and_pending_dependent_task_block(self):
        other = copy.deepcopy(self.task)
        other["id"] = "B-other"
        self.tasks.append(other)
        self.status("blocked")
        other.update(worktree=str(self.repo / ".worktrees/B-other"), status="pending", depends_on=[self.task["id"]])
        self.status("blocked")

    def test_absent_incomplete_stale_future_and_missing_thread_are_unknown(self):
        original = copy.deepcopy(self.activity)
        for value in (None, {}, {**original, "complete": False}, {**original, "threads": []},
                      {**original, "captured_at": (self.now - timedelta(minutes=6)).isoformat()},
                      {**original, "captured_at": (self.now + timedelta(seconds=1)).isoformat()}):
            with self.subTest(value=value):
                self.activity = value
                self.status("unknown")

    def test_active_registered_or_unregistered_thread_blocks(self):
        for status in ("running", "waiting", "planning"):
            self.activity["threads"][0]["status"] = status
            self.status("blocked")
        self.activity["threads"][0]["status"] = "idle"
        self.activity["threads"].append({"id": "other", "worktree": str(self.wt), "status": "running"})
        self.status("blocked")

    def test_task_must_be_completed(self):
        self.task["status"] = "active"
        self.status("blocked")

    def test_changed_missing_archive_or_empty_review_is_unknown(self):
        path = self.archive / "PRD.md"
        path.write_text("changed")
        self.status("unknown")
        path.unlink()
        self.status("unknown")

    def test_missing_bundle_or_review_is_unknown(self):
        for name in ("head.bundle", "reviews/codex.md"):
            saved = (self.archive / name).read_bytes()
            (self.archive / name).unlink()
            self.refresh_manifest()
            self.status("unknown")
            (self.archive / name).write_bytes(saved)
            self.refresh_manifest()

    def test_corrupt_and_truncated_bundle_payloads_are_unknown(self):
        path = self.archive / "head.bundle"
        original = path.read_bytes()
        pack = original.index(b"PACK")
        for content in (original[:-20], original[:pack + 20] + bytes([original[pack + 20] ^ 255]) + original[pack + 21:]):
            with self.subTest(length=len(content)):
                path.write_bytes(content)
                self.refresh_manifest()
                self.status("unknown")

    def test_real_task_directory_and_wrong_link_block(self):
        (self.wt / ".task").unlink()
        (self.wt / ".task").mkdir()
        self.status("blocked")
        (self.wt / ".task").rmdir()
        (self.wt / ".task").symlink_to(self.records, target_is_directory=True)
        self.status("blocked")

    def test_archive_symlink_escape_is_unknown(self):
        (self.archive / "PRD.md").unlink()
        (self.archive / "PRD.md").symlink_to(self.wt / "seed")
        self.refresh_manifest()
        self.status("unknown")

    def test_protected_and_symlinked_targets_never_eligible(self):
        for target in (self.repo, self.repo / ".worktrees", self.records):
            self.task["worktree"] = str(target)
            self.assertNotEqual(self.run_audit()["tasks"][0]["status"], "eligible")
        link = self.repo / ".worktrees/B-link"
        link.symlink_to(self.wt, target_is_directory=True)
        self.task["worktree"] = str(link)
        self.assertNotEqual(self.run_audit()["tasks"][0]["status"], "eligible")

    def test_changed_pr_git_archive_or_control_during_audit_is_unknown(self):
        for kind in ("pr", "git", "archive", "control", "link"):
            with self.subTest(kind=kind):
                calls = []
                def api(endpoint):
                    calls.append(endpoint)
                    value = copy.deepcopy(self.responses[endpoint])
                    if calls.count("repos/ente-io/ente/pulls/20") == 2:
                        if kind == "pr":
                            value["state"] = "open"
                        elif kind == "git":
                            (self.wt / "seed").write_text("racing write")
                        elif kind == "archive":
                            (self.archive / "PRD.md").write_text("racing write")
                        elif kind == "link":
                            (self.wt / ".task").unlink()
                            (self.wt / ".task").symlink_to(self.records, target_is_directory=True)
                        else:
                            (self.records / "control.json").write_text("{}")
                    return value
                self.status("unknown", api)
                (self.wt / "seed").write_text("original\n")
                (self.archive / "PRD.md").write_text("Reviewed fixture\n")
                (self.wt / ".task").unlink()
                (self.wt / ".task").symlink_to(self.archive, target_is_directory=True)

    def test_malformed_task_and_response_are_unknown(self):
        original = copy.deepcopy(self.task)
        for key, value in (("fork", None), ("thread_ids", "bad"), ("archive", {}), ("head_sha", "short"), ("mapping_evidence", "")):
            self.tasks = [{**original, key: value}]
            self.status("unknown")
        self.tasks = [original]
        self.status("unknown", lambda endpoint: None)

    def test_closed_fork_requires_no_close_action(self):
        self.responses["repos/AmanRajSinghMourya/ente/pulls/10"]["state"] = "closed"
        result = self.status("eligible")
        self.assertEqual(len(result["proposed_actions"]), 2)


if __name__ == "__main__":
    unittest.main()
