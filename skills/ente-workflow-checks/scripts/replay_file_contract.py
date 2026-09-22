#!/usr/bin/env python3
"""Real filesystem/Git replays of approved scope, restoration and copy checks."""

import json
from pathlib import Path
import subprocess
import tempfile
import unittest

import check_file_contract
import checks


class FileContractReplay(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="file-contract-replay-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.name", "Test Author")
        self.git("config", "user.email", "test@example.invalid")
        for name, content in {"v1.dart": "reference\n", "v2.dart": "target\n", "en.arb": '{"photo":"Photo"}\n', "fr.arb": '{"photo":"Photo"}\n'}.items():
            (self.repo / name).write_text(content)
        self.git("add", ".")
        self.git("commit", "-q", "-m", "fixture base")
        self.contract = {"repo": str(self.repo), "branch": "main", "base": self.git("rev-parse", "HEAD").strip(), "allowed_paths": ["v2.dart", "en.arb", "changes/*.md"]}

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.repo), "-c", "core.hooksPath=/dev/null", "-c", "commit.gpgsign=false", *args], check=True, capture_output=True, text=True).stdout

    def verify(self, repo=None):
        return check_file_contract.verify(repo or self.repo, self.contract)

    def fails(self, name):
        result = self.verify()
        self.assertEqual(result["status"], "fail")
        self.assertTrue(any(c["check"] == name and c["status"] == "fail" for c in result["checks"]))

    def test_valid_target_edit_preserves_reference(self):
        self.contract["files"] = [{"path": "v1.dart", "sha256": checks.file_hash(self.repo / "v1.dart")}]
        (self.repo / "v2.dart").write_text("approved new target\n")
        self.assertEqual(self.verify()["status"], "pass")

    def test_wrong_checkout_with_same_files_fails(self):
        other = self.root / "other"
        subprocess.run(["git", "clone", "-q", str(self.repo), str(other)], check=True)
        self.assertEqual(self.verify(other)["status"], "fail")

    def test_wrong_revision_fails(self):
        self.contract["head"] = self.contract["base"]
        (self.repo / "v2.dart").write_text("next\n")
        self.git("add", "v2.dart")
        self.git("commit", "-q", "-m", "next fixture")
        self.fails("selected_revision")

    def test_edit_to_reference_fails(self):
        (self.repo / "v1.dart").write_text("wrong component\n")
        self.fails("permitted_file")

    def test_translator_locale_change_fails(self):
        (self.repo / "fr.arb").write_text("{}\n")
        self.fails("permitted_file")

    def test_english_only_cleanup_passes(self):
        (self.repo / "en.arb").write_text("{}\n")
        self.assertEqual(self.verify()["status"], "pass")

    def test_index_change_cannot_hide_behind_restored_worktree(self):
        reference = self.repo / "v1.dart"
        original = reference.read_bytes()
        reference.write_text("staged unrelated edit\n")
        self.git("add", "v1.dart")
        reference.write_bytes(original)
        self.fails("permitted_file")

    def test_frozen_restoration_requires_every_file(self):
        del self.contract["allowed_paths"]
        self.contract["files"] = [{"path": p, "sha256": checks.file_hash(self.repo / p)} for p in ("v1.dart", "v2.dart")]
        (self.repo / "v1.dart").unlink()
        self.fails("required_file_exists")
        (self.repo / "v1.dart").write_text("reference\n")
        self.assertEqual(self.verify()["status"], "pass")

    def test_staged_wrong_contents_fail_even_on_permitted_file(self):
        self.contract["files"] = [{"path": "v2.dart", "text": "target\n"}]
        target = self.repo / "v2.dart"
        target.write_text("unapproved staged content\n")
        self.git("add", "v2.dart")
        target.write_text("target\n")
        self.fails("staged_file_matches_worktree")

    def test_staged_wrapper_cannot_hide_by_removing_disk_copy(self):
        self.contract["allowed_paths"].append("old_wrapper.dart")
        self.contract["files"] = [{"path": "old_wrapper.dart", "absent": True}]
        wrapper = self.repo / "old_wrapper.dart"
        wrapper.write_text("recreated\n")
        self.git("add", "old_wrapper.dart")
        wrapper.unlink()
        self.fails("staged_file_matches_worktree")

    def test_unstaged_new_approved_copy_is_valid_pending_work(self):
        self.contract["files"] = [{"path": "en.arb", "json_values": {"photo": "New approved copy"}}]
        (self.repo / "en.arb").write_text(json.dumps({"photo": "New approved copy"}))
        self.assertEqual(self.verify()["status"], "pass")
        self.git("add", "en.arb")
        self.assertEqual(self.verify()["status"], "pass")

    def test_intentionally_removed_wrapper_must_stay_absent(self):
        self.contract["allowed_paths"].append("old_wrapper.dart")
        self.contract["files"] = [{"path": "old_wrapper.dart", "absent": True}]
        self.assertEqual(self.verify()["status"], "pass")
        (self.repo / "old_wrapper.dart").write_text("recreated\n")
        self.fails("intentional_absence")

    def test_approved_copy_fails_on_drift_and_passes_after_explicit_new_choice(self):
        self.contract["files"] = [{"path": "en.arb", "json_values": {"photo": "Photo"}}]
        (self.repo / "en.arb").write_text(json.dumps({"photo": "Image"}))
        self.fails("approved_json_value:photo")
        self.contract["files"][0]["json_values"]["photo"] = "Image"
        self.assertEqual(self.verify()["status"], "pass")

    def test_release_note_in_wrong_document_does_not_pass(self):
        self.contract["files"] = [{"path": "changes/feature.md", "text": "Approved release bullet\n"}]
        self.contract["must_change"] = ["changes/feature.md"]
        (self.repo / "notes.md").write_text("Approved release bullet\n")
        self.fails("required_file_exists")
        self.fails("required_changed_file")

    def test_approved_release_fragment_passes(self):
        self.contract["files"] = [{"path": "changes/feature.md", "text": "Approved release bullet\n"}]
        self.contract["must_change"] = ["changes/feature.md"]
        (self.repo / "changes").mkdir()
        (self.repo / "changes/feature.md").write_text("Approved release bullet\n")
        self.assertEqual(self.verify()["status"], "pass")

    def test_wrong_document_link_fails(self):
        self.contract["files"] = [{"path": "en.arb", "json_values": {"photo": "Photo"}}]
        (self.repo / "en.arb").unlink()
        (self.repo / "en.arb").symlink_to("fr.arb")
        self.fails("exact_file_location")

    def test_unknown_assertion_and_moving_base_do_not_pass(self):
        self.contract["base"] = "main"
        with self.assertRaises(ValueError):
            self.verify()
        self.contract["base"] = self.git("rev-parse", "HEAD").strip()
        self.contract["filez"] = []
        with self.assertRaises(ValueError):
            self.verify()


if __name__ == "__main__":
    unittest.main(verbosity=2)
