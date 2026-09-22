#!/usr/bin/env python3
"""Replay historical failure shapes and valid controls in disposable Git repositories.

These are real local Git/command executions with simulated GitHub read responses.
They do not recreate historical Ente implementations or contact GitHub.
"""

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import checks


class Replay(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="workflow-replay-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self.g("init", "-q", "-b", "main")
        self.g("config", "user.name", "Test Author")
        self.g("config", "user.email", "test@example.invalid")
        self.source = self.repo / "mobile/apps/photos/feature.dart"
        self.source.parent.mkdir(parents=True)
        self.source.write_text("base\n")
        self.commit("base")
        self.old_base = self.g("rev-parse", "HEAD").strip()
        (self.repo / "server").mkdir()
        (self.repo / "server/unrelated.go").write_text("upstream change\n")
        self.commit("upstream advance")
        self.base = self.g("rev-parse", "HEAD").strip()
        self.g("checkout", "-q", "-b", "aman/photos-example")
        self.source.write_text("feature\n")
        self.commit("feature")
        self.url = "git@github-main:example-fork/ente.git"
        self.g("remote", "add", "origin", self.url)
        self.contract = {
            "branch": "aman/photos-example", "remote": "origin", "push_url": self.url,
            "target_repo": "example-fork/ente", "head_repo": "example-fork/ente",
            "upstream_repo": "example-upstream/ente", "base_branch": "main",
            "match_upstream": True, "api_login": "test-user",
            "author": {"name": "Test Author", "email": "test@example.invalid"},
            "allowed_paths": ["mobile/apps/photos/feature.dart"],
        }
        self.login = "test-user"
        self.remote_head = None
        self.target_base = self.base
        self.pr_head_repo = "example-fork/ente"

    def g(self, *args):
        result = subprocess.run(["git", "-C", str(self.repo), "-c", "core.hooksPath=/dev/null", "-c", "commit.gpgsign=false", *args], capture_output=True, text=True)
        if result.returncode:
            raise AssertionError(result.stderr)
        return result.stdout

    def commit(self, message):
        self.g("add", ".")
        self.g("commit", "-q", "-m", message)

    def api(self, endpoint):
        if endpoint == "user":
            return {"login": self.login}
        if endpoint.startswith("repos/") and endpoint.count("/") == 2:
            return {"full_name": endpoint[len("repos/"):].replace("example-legacy/", "example-fork/")}
        if endpoint.endswith("/pulls/1"):
            return {"base": {"repo": {"full_name": "example-fork/ente"}, "ref": "main"}, "head": {"repo": {"full_name": self.pr_head_repo}, "ref": self.contract["branch"], "sha": self.g("rev-parse", "HEAD").strip()}}
        if endpoint.endswith("/heads/main"):
            sha = self.target_base if "example-fork/" in endpoint else self.base
            return {"ref": "refs/heads/main", "object": {"type": "commit", "sha": sha}}
        if endpoint.endswith("/heads/aman%2Fphotos-example"):
            return {"ref": "refs/heads/aman/photos-example", "object": {"type": "commit", "sha": self.remote_head or self.g("rev-parse", "HEAD").strip()}}
        raise AssertionError("Unexpected API request: " + endpoint)

    def preflight(self):
        before = checks.investigation_state(self.repo)
        result = checks.preflight(self.repo, self.contract, api=self.api)
        self.assertEqual(before, checks.investigation_state(self.repo), "preflight mutated the repository")
        return result

    def fails(self, result, name):
        self.assertEqual(result["status"], "fail")
        self.assertEqual(next(c for c in result["checks"] if c["check"] == name)["status"], "fail")

    def test_clean_feature_passes(self):
        self.assertEqual(self.preflight()["status"], "pass")

    def test_stale_fork_reveals_unrelated_history(self):
        self.target_base = self.old_base
        result = self.preflight()
        self.fails(result, "fork_base_matches_upstream")
        self.fails(result, "change_scope")

    def test_extra_commit_in_allowed_file_is_rejected(self):
        self.contract["expected_commits"] = [self.g("rev-parse", "HEAD").strip()]
        self.source.write_text("unwanted extra change in the same file\n")
        self.commit("unwanted extra commit")
        result = self.preflight()
        self.assertEqual(next(c for c in result["checks"] if c["check"] == "change_scope")["status"], "pass")
        self.fails(result, "candidate_commits")

    def test_selected_multi_commit_candidate_passes(self):
        first = self.g("rev-parse", "HEAD").strip()
        self.source.write_text("intended second step\n")
        self.commit("intended second step")
        self.contract["expected_commits"] = [first, self.g("rev-parse", "HEAD").strip()]
        result = self.preflight()
        self.assertEqual(result["status"], "pass")
        self.assertEqual(next(c for c in result["checks"] if c["check"] == "candidate_commits")["status"], "pass")

    def test_missing_selected_commit_is_rejected(self):
        self.contract["expected_commits"] = [self.g("rev-parse", "HEAD").strip(), self.base]
        self.fails(self.preflight(), "candidate_commits")

    def test_valid_thirty_commit_feature_is_not_rejected_for_size(self):
        for number in range(29):
            self.source.write_text("feature %d\n" % number)
            self.commit("feature step %d" % number)
        self.assertEqual(self.preflight()["status"], "pass")

    def test_renamed_file_checks_both_paths(self):
        self.source.rename(self.source.with_name("renamed.dart"))
        self.commit("rename")
        self.fails(self.preflight(), "change_scope")

    def test_wrong_api_account_does_not_hide_behind_correct_ssh_url(self):
        self.login = "another-account"
        self.fails(self.preflight(), "github_api_account")

    def test_wrong_remote_is_detected(self):
        self.g("remote", "set-url", "origin", "git@github-main:another-fork/ente.git")
        self.fails(self.preflight(), "push_destination")

    def test_contract_with_wrong_push_repository_is_rejected(self):
        self.contract["head_repo"] = "different-fork/ente"
        self.fails(self.preflight(), "push_url_matches_head_repository")

    def test_existing_pr_in_other_fork_is_detected(self):
        self.contract["pr_number"] = 1
        self.pr_head_repo = "another-fork/ente"
        self.fails(self.preflight(), "existing_pr_identity")

    def test_github_repository_redirect_is_not_a_false_mismatch(self):
        self.contract["target_repo"] = "example-legacy/ente"
        self.contract["head_repo"] = "example-legacy/ente"
        self.contract["pr_number"] = 1
        self.assertEqual(self.preflight()["status"], "pass")

    def test_unpushed_head_is_detected(self):
        self.remote_head = self.base
        self.fails(self.preflight(), "pushed_head")

    def test_replacement_ref_cannot_hide_out_of_scope_change(self):
        (self.repo / "server/unrelated.go").write_text("forbidden change\n")
        self.commit("out of scope")
        head = self.g("rev-parse", "HEAD").strip()
        self.g("checkout", "-q", "--detach", self.base)
        (self.repo / "server/unrelated.go").write_text("forbidden change\n")
        self.commit("replacement tree")
        replacement = self.g("rev-parse", "HEAD").strip()
        self.g("checkout", "-q", "aman/photos-example")
        self.g("replace", self.base, replacement)
        self.assertEqual(self.g("rev-parse", "HEAD").strip(), head)
        self.fails(self.preflight(), "change_scope")

    def test_wrong_branch_is_detected(self):
        self.g("checkout", "-q", "-b", "aman/other-task")
        self.fails(self.preflight(), "task_branch")

    def test_uncommitted_work_cannot_be_called_published(self):
        self.source.write_text("unpublished fix\n")
        self.fails(self.preflight(), "published_code_is_working_code")

    def test_offline_is_incomplete_never_a_full_pass(self):
        self.assertEqual(checks.preflight(self.repo, self.contract, offline=True)["status"], "incomplete")

    def test_successful_command_receipt_matches_current_source(self):
        receipt = self.root / "check.json"
        result = checks.run_validation(self.repo, ".", receipt, [sys.executable, "-c", "print('verified')"])
        self.assertEqual(result["status"], "pass")
        self.assertEqual(checks.verify_validation(self.repo, receipt)["status"], "pass")

    def test_code_edit_invalidates_green_receipt(self):
        receipt = self.root / "check.json"
        checks.run_validation(self.repo, ".", receipt, [sys.executable, "-c", "print('verified')"])
        self.source.write_text("later edit\n")
        self.fails(checks.verify_validation(self.repo, receipt), "source_still_matches")

    def test_new_file_invalidates_green_receipt(self):
        receipt = self.root / "check.json"
        checks.run_validation(self.repo, ".", receipt, [sys.executable, "-c", "print('verified')"])
        (self.repo / "new_source.dart").write_text("new code")
        self.fails(checks.verify_validation(self.repo, receipt), "source_still_matches")

    def test_failing_command_is_not_a_green_receipt(self):
        receipt = self.root / "check.json"
        result = checks.run_validation(self.repo, ".", receipt, [sys.executable, "-c", "raise SystemExit(7)"])
        self.assertEqual(result["exit_code"], 7)
        self.fails(checks.verify_validation(self.repo, receipt), "command_passed")

    def test_command_that_changes_source_is_not_green(self):
        receipt = self.root / "check.json"
        result = checks.run_validation(self.repo, ".", receipt, [sys.executable, "-c", "from pathlib import Path; Path('mobile/apps/photos/feature.dart').write_text('changed')"])
        self.assertEqual(result["status"], "fail")

    def test_investigation_allows_preexisting_dirty_state_without_changing_it(self):
        self.source.write_text("user's existing work\n")
        before = checks.investigation_state(self.repo)
        self.g("ls-files")
        self.assertEqual(before, checks.investigation_state(self.repo))
        self.assertEqual(self.source.read_text(), "user's existing work\n")

    def test_investigation_catches_source_edit(self):
        before = checks.investigation_state(self.repo)
        self.source.write_text("unrequested fix\n")
        self.assertNotEqual(before, checks.investigation_state(self.repo))

    def test_investigation_catches_index_only_change(self):
        before = checks.investigation_state(self.repo)
        original = self.source.read_text()
        self.source.write_text("staged replacement\n")
        self.g("add", str(self.source))
        self.source.write_text(original)
        self.assertEqual(before["changes_sha256"], checks.investigation_state(self.repo)["changes_sha256"])
        self.assertNotEqual(before["index_sha256"], checks.investigation_state(self.repo)["index_sha256"])

    def test_index_only_change_invalidates_green_receipt(self):
        receipt = self.root / "check.json"
        checks.run_validation(self.repo, ".", receipt, [sys.executable, "-c", "pass"])
        original = self.source.read_text()
        self.source.write_text("staged replacement\n")
        self.g("add", str(self.source))
        self.source.write_text(original)
        self.fails(checks.verify_validation(self.repo, receipt), "source_still_matches")

    def test_hidden_git_changes_are_incomplete_not_green(self):
        self.g("update-index", "--assume-unchanged", str(self.source))
        self.source.write_text("hidden edit\n")
        with self.assertRaisesRegex(ValueError, "hide changes"):
            checks.fingerprint(self.repo)

    def test_receipt_must_be_outside_repository(self):
        with self.assertRaisesRegex(ValueError, "outside"):
            checks.run_validation(self.repo, ".", self.repo / "receipt.json", [sys.executable, "-c", "pass"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
