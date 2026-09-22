#!/usr/bin/env python3
"""Replay PRD and task-size boundaries using disposable files and repositories."""

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

import check_task


class PrdReplay(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="task-prd-replay-")
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "PRD.md"

    def test_utf8_byte_boundaries(self):
        for content, status in (("a" * 50000, "pass"), ("é" * 25000, "pass"), ("é" * 25001, "fail")):
            with self.subTest(bytes=len(content.encode())):
                self.path.write_text(content, encoding="utf-8")
                result = check_task.check_prd(self.path)
                self.assertEqual(result["status"], status)
                self.assertEqual(result["bytes"], len(content.encode()))

    def test_digest_rejects_changed_prd(self):
        original = b"Agreed behavior\n"
        digest = hashlib.sha256(original).hexdigest()
        self.path.write_bytes(original)
        self.assertEqual(check_task.check_prd(self.path, digest)["status"], "pass")
        self.path.write_text("Different behavior\n")
        self.assertEqual(check_task.check_prd(self.path, digest)["status"], "fail")

    def test_empty_documents_fail(self):
        for content in (b"", b" \n\t"):
            self.path.write_bytes(content)
            self.assertEqual(check_task.check_prd(self.path)["status"], "fail")

    def test_read_and_decode_errors_are_incomplete(self):
        self.assertEqual(cli("prd", "--prd", str(self.path)), (2, "incomplete"))
        self.path.write_bytes(b"\xff")
        self.assertEqual(cli("prd", "--prd", str(self.path)), (2, "incomplete"))

    def test_cli_exit_codes(self):
        self.path.write_text("A concise requirement")
        self.assertEqual(cli("prd", "--prd", str(self.path)), (0, "pass"))
        self.assertEqual(cli("prd", "--prd", str(self.path), "--sha256", "0" * 64), (1, "fail"))

    def test_cli_without_bytecode_flag_does_not_write_cache(self):
        scripts = Path(self.temp.name) / "scripts"
        scripts.mkdir()
        for name in ("check_task.py", "checks.py"):
            shutil.copy2(Path(check_task.__file__).parent / name, scripts / name)
        self.path.write_text("A concise requirement")
        env = dict(os.environ)
        env.pop("PYTHONDONTWRITEBYTECODE", None)
        env.pop("PYTHONPYCACHEPREFIX", None)
        launch = "import runpy,sys; sys.pycache_prefix=None; sys.path.insert(0,sys.argv[1]); sys.argv=sys.argv[1:]; sys.argv[0]+='/check_task.py'; runpy.run_path(sys.argv[0],run_name='__main__')"
        result = subprocess.run([sys.executable, "-c", launch, str(scripts), "prd", "--prd", str(self.path)], env=env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((scripts / "__pycache__").exists())


class DiffReplay(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="task-diff-replay-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.name", "Replay Author")
        self.git("config", "user.email", "replay@example.invalid")
        (self.repo / "seed").write_text("one\ntwo\n")
        self.git("add", ".")
        self.git("commit", "-q", "-m", "fixture base")
        self.base = self.git("rev-parse", "HEAD").strip()

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.repo), "-c", "core.hooksPath=/dev/null", "-c", "commit.gpgsign=false", *args], check=True, capture_output=True, text=True).stdout

    def measure(self):
        return check_task.measure_diff(self.repo, self.base)

    def test_tracked_staged_deleted_and_untracked(self):
        (self.repo / "seed").unlink()
        (self.repo / "staged").write_text("new\n" * 4)
        self.git("add", "staged")
        (self.repo / "untracked").write_text("another\n" * 3)
        result = self.measure()
        self.assertEqual((result["added_lines"], result["deleted_lines"], result["changed_lines"]), (7, 2, 9))
        self.assertEqual({f["path"] for f in result["files"]}, {"seed", "staged", "untracked"})

    def test_divergent_staged_and_worktree_versions_are_incomplete(self):
        (self.repo / "seed").write_text("staged\n")
        self.git("add", "seed")
        (self.repo / "seed").write_text("final\n")
        self.assertEqual(cli("diff", "--repo", str(self.repo), "--base", self.base), (2, "incomplete"))

    def test_oversized_staged_change_cannot_hide_behind_restored_disk(self):
        (self.repo / "seed").write_text("large staged change\n" * 1001)
        self.git("add", "seed")
        (self.repo / "seed").write_text("one\ntwo\n")
        self.assertEqual(cli("diff", "--repo", str(self.repo), "--base", self.base), (2, "incomplete"))

    def test_rename_counts_delete_and_add(self):
        self.git("mv", "seed", "renamed")
        result = self.measure()
        self.assertEqual(result["changed_lines"], 4)
        self.assertEqual({f["path"] for f in result["files"]}, {"seed", "renamed"})

    def test_odd_filename_survives_numstat(self):
        name = "space tab\tand newline\n.txt"
        (self.repo / name).write_text("new\nlast")
        result = self.measure()
        self.assertEqual(result["files"][0]["path"], name)
        self.assertEqual(result["changed_lines"], 2)
        self.git("add", name)
        self.assertEqual(self.measure()["changed_lines"], 2)

    def test_symlink_counts_link_not_target(self):
        target = self.root / "outside"
        target.write_text("large\n" * 2000)
        (self.repo / "link").symlink_to(target)
        self.assertEqual(self.measure()["changed_lines"], 1)
        target.unlink()
        self.assertEqual(self.measure()["changed_lines"], 1)

    def test_ignored_file_excluded(self):
        (self.repo / ".gitignore").write_text("ignored\n")
        (self.repo / "ignored").write_text("noise\n" * 1001)
        self.assertEqual(self.measure()["changed_lines"], 1)

    def test_empty_untracked_file_is_reported(self):
        (self.repo / "empty").touch()
        result = self.measure()
        self.assertEqual(result["changed_lines"], 0)
        self.assertEqual(result["files"][0]["path"], "empty")

    def test_index_deletion_with_untracked_replacement_is_incomplete(self):
        self.git("rm", "--cached", "seed")
        self.assertEqual(cli("diff", "--repo", str(self.repo), "--base", self.base), (2, "incomplete"))

    def test_line_thresholds(self):
        for lines, status, warning in ((500, "pass", False), (501, "pass", True), (1000, "pass", True), (1001, "fail", True)):
            with self.subTest(lines=lines):
                (self.repo / "new").write_text("line\n" * lines)
                result = self.measure()
                self.assertEqual((result["changed_lines"], result["status"], bool(result["warnings"])), (lines, status, warning))

    def test_binary_is_incomplete_for_untracked_and_tracked(self):
        (self.repo / "binary").write_bytes(b"\x00data")
        self.assertEqual(self.measure()["status"], "incomplete")
        self.assertEqual(self.measure()["binaries"], ["binary"])
        self.git("add", "binary")
        self.assertEqual(self.measure()["status"], "incomplete")

    def test_known_oversize_fails_even_with_binary(self):
        (self.repo / "new").write_text("line\n" * 1001)
        (self.repo / "binary").write_bytes(b"\x00data")
        self.assertEqual(self.measure()["status"], "fail")

    def test_hidden_git_flags_are_incomplete(self):
        for flag in ("assume-unchanged", "skip-worktree"):
            self.git("update-index", "--" + flag, "seed")
            self.assertEqual(cli("diff", "--repo", str(self.repo), "--base", self.base), (2, "incomplete"))
            self.git("update-index", "--no-" + flag, "seed")

    def test_dirty_submodule_is_incomplete(self):
        source = self.root / "subsource"
        subprocess.run(["git", "clone", "-q", str(self.repo), str(source)], check=True)
        self.git("-c", "protocol.file.allow=always", "submodule", "add", "-q", str(source), "sub")
        self.git("commit", "-q", "-m", "fixture submodule")
        (self.repo / "sub" / "new").write_text("dirty\n")
        self.assertEqual(cli("diff", "--repo", str(self.repo), "--base", self.base), (2, "incomplete"))

    def test_bad_repo_base_and_nonancestor_are_incomplete(self):
        for base in ("main", "0" * 40):
            self.assertEqual(cli("diff", "--repo", str(self.repo), "--base", base), (2, "incomplete"))
        nested = self.repo / "nested"
        nested.mkdir()
        self.assertEqual(cli("diff", "--repo", str(nested), "--base", self.base), (2, "incomplete"))
        self.git("checkout", "-q", "--orphan", "unrelated")
        self.git("commit", "-q", "-m", "different fixture root")
        self.assertEqual(cli("diff", "--repo", str(self.repo), "--base", self.base), (2, "incomplete"))


def cli(*args):
    result = subprocess.run([sys.executable, "-B", str(Path(check_task.__file__)), *args], capture_output=True, text=True)
    return result.returncode, json.loads(result.stdout)["status"]


if __name__ == "__main__":
    unittest.main(verbosity=2)
