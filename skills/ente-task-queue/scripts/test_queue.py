import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).with_name("queue.py")
SPEC = importlib.util.spec_from_file_location("task_queue", SCRIPT)
QUEUE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(QUEUE)
THREAD = "12345678-1234-1234-1234-123456789abc"
OTHER_THREAD = "87654321-4321-4321-4321-cba987654321"
PREFIX = "# Shared queue\r\n\r\nInstructions stay unchanged.\r\n"
SUFFIX = "\r\n\r\nFooter stays unchanged.\r\n"
TABLE = (
    "| ID | Task | Status | Codex task | Context |\n"
    "| --- | --- | --- | --- | --- |\n"
)
EMPTY = PREFIX + "<!-- queue:start -->\n" + TABLE + "<!-- queue:end -->" + SUFFIX


class QueueTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "TODO.md"
        self.path.write_bytes(EMPTY.encode())

    def command(self, *args):
        return [sys.executable, str(SCRIPT), "--file", str(self.path), *args]

    def call(self, *args):
        result = subprocess.run(self.command(*args), capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def reject(self, *args):
        original = self.path.read_bytes()
        result = subprocess.run(self.command(*args), capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(result.stderr.strip())
        self.assertEqual(self.path.read_bytes(), original)
        return result.stderr

    def parallel(self, commands):
        processes = [
            subprocess.Popen(self.command(*args), stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, text=True)
            for args in commands
        ]
        completed = [(process, process.communicate(timeout=15)) for process in processes]
        results = []
        for process, (stdout, stderr) in completed:
            self.assertEqual(process.returncode, 0, stderr)
            results.append(json.loads(stdout))
        return results

    def add(self, title="Fix the album view", context="Source: issue 42", *extra):
        return self.call("add", "--title", title, "--context", context, *extra)

    def test_add_and_hold_preserve_surrounding_bytes(self):
        self.assertEqual(self.call("list"), [])
        self.assertEqual(self.add()["id"], "Q001")
        held = self.add("Later work", "Details", "--hold")
        self.assertEqual((held["id"], held["status"], held["codex_task"]),
                         ("Q002", "deferred", ""))
        raw = self.path.read_bytes()
        self.assertTrue(raw.startswith((PREFIX + "<!-- queue:start -->").encode()))
        self.assertTrue(raw.endswith(("<!-- queue:end -->" + SUFFIX).encode()))

    def test_direct_tracking_starts_planning_and_is_excluded_from_claim(self):
        tracked = self.add("Already in this chat", "Original context", "--thread", THREAD.upper())
        self.assertEqual((tracked["id"], tracked["status"], tracked["codex_task"]),
                         ("Q001", "planning", f"codex://threads/{THREAD}"))
        self.add("Waiting for a chat")
        self.assertEqual(self.call("claim")["id"], "Q002")
        self.assertIsNone(self.call("claim"))
        self.assertEqual(self.call("list")[0], tracked)

    def test_direct_tracking_reregistration_preserves_latest_status_and_context(self):
        self.add("Already in this chat", "Original context", "--thread", THREAD)
        self.add("Another task", "Independent context")
        current = self.call("state", "Q001", "--from", "planning", "--to", "implementing")
        original = self.path.read_bytes()
        repeated = self.add("Another task", "Replacement context", "--thread", THREAD)
        self.assertEqual(repeated, current)
        self.assertEqual(self.path.read_bytes(), original)
        self.reject("add", "--title", " \n\t", "--context", "Replacement context",
                    "--thread", THREAD)

    def test_direct_tracking_concurrent_registration_creates_one_row(self):
        results = self.parallel([
            ("add", "--title", f"Task {index}", "--context", f"Context {index}",
             "--thread", THREAD)
            for index in range(8)
        ])
        self.assertTrue(all(row == results[0] for row in results))
        self.assertEqual(self.call("list"), [results[0]])
        self.assertEqual((results[0]["id"], results[0]["status"]), ("Q001", "planning"))

    def test_direct_tracking_rejects_hold_and_invalid_inputs_without_mutation(self):
        self.add()
        error = self.reject("add", "--title", "Direct task", "--context", "Context",
                            "--thread", THREAD, "--hold")
        self.assertIn("--hold", error)
        for identifier in ("not-a-uuid", ""):
            with self.subTest(identifier=identifier):
                error = self.reject("add", "--title", "Direct task", "--context", "Context",
                                    "--thread", identifier)
                self.assertIn("invalid thread UUID", error)
        error = self.reject("add", "--title", " \n\t", "--context", "Context",
                            "--thread", THREAD)
        self.assertIn("title must not be empty", error)

    def test_direct_tracking_rejects_conflicting_title_for_another_thread(self):
        self.add("Fix THE album view", "Original context", "--thread", THREAD)
        error = self.reject("add", "--title", "  fix the  ALBUM view\n",
                            "--context", "Another context", "--thread", OTHER_THREAD)
        self.assertIn("title already exists as Q001", error)

    def test_human_cells_roundtrip_without_table_or_html_injection(self):
        title = "  Spec | <script> & &#124;\nΔ  "
        context = "\t<br> literal | &amp;\r\n[reference](https://example.test)\t "
        self.add(title, context)
        row = self.call("list")[0]
        self.assertEqual((row["task"], row["context"]), (title, context))
        raw = self.path.read_text()
        self.assertNotIn("<script>", raw)
        self.assertNotIn("<br>", raw)
        self.assertIn("&#124;", raw)
        block = raw.split("<!-- queue:start -->")[1].split("<!-- queue:end -->")[0]
        self.assertEqual(len(block.splitlines()), 4)

    def test_empty_and_duplicate_titles_are_rejected_without_losing_context(self):
        self.reject("add", "--title", " \n\t", "--context", "Keep me")
        self.add("Fix THE album view")
        error = self.reject("add", "--title", "  fix the  ALBUM view\n",
                            "--context", "New context must not disappear")
        self.assertIn("Q001", error)
        self.assertIn("context", error.lower())

    def test_concurrent_adds_do_not_lose_rows(self):
        results = self.parallel([
            ("add", "--title", f"Task {index}", "--context", f"Context {index}")
            for index in range(12)
        ])
        rows = self.call("list")
        self.assertEqual(len(rows), 12)
        self.assertEqual({row["id"] for row in results},
                         {f"Q{index:03}" for index in range(1, 13)})
        self.assertEqual({row["task"] for row in rows},
                         {f"Task {index}" for index in range(12)})

    def test_competing_claims_have_one_winner_per_item(self):
        for index in range(5):
            self.add(f"Task {index}")
        results = self.parallel([("claim",)] * 10)
        claimed = [row for row in results if row is not None]
        self.assertEqual(len(claimed), 5)
        self.assertEqual(len({row["id"] for row in claimed}), 5)
        self.assertTrue(all(row["status"] == "starting" for row in claimed))

    def test_claim_skips_deferred_and_never_redispatches_starting(self):
        self.add("Held", "", "--hold")
        self.add("First")
        self.add("Second")
        self.assertEqual(self.call("claim")["id"], "Q002")
        self.assertEqual(self.call("claim")["id"], "Q003")
        self.assertIsNone(self.call("claim"))
        self.assertEqual([row["status"] for row in self.call("list")],
                         ["deferred", "starting", "starting"])

    def test_starting_cannot_be_directly_requeued(self):
        self.add()
        self.call("claim")
        error = self.reject("state", "Q001", "--from", "starting", "--to", "queued")
        self.assertIn("reconcile the existing dispatch first", error)

    def test_attach_is_idempotent_and_conflicts_are_rejected(self):
        self.add()
        self.reject("attach", "Q001", "--thread", THREAD)
        self.call("claim")
        self.reject("attach", "Q001", "--thread", "not-a-uuid")
        attached = self.call("attach", "Q001", "--thread", THREAD)
        self.assertEqual(attached["status"], "planning")
        self.assertEqual(attached["codex_task"], f"codex://threads/{THREAD}")
        original = self.path.read_bytes()
        self.assertEqual(self.call("attach", "Q001", "--thread", THREAD), attached)
        self.assertEqual(self.path.read_bytes(), original)
        self.reject("attach", "Q001", "--thread", OTHER_THREAD)
        self.call("state", "Q001", "--from", "planning", "--to", "implementing")
        self.assertEqual(self.call("attach", "Q001", "--thread", THREAD)["status"],
                         "implementing")

    def test_compare_and_set_and_state_constraints(self):
        self.add()
        self.reject("state", "Q001", "--from", "deferred", "--to", "queued")
        for status in ("starting", "planning", "needs decision", "implementing",
                       "ready for review", "done"):
            self.reject("state", "Q001", "--from", "queued", "--to", status)
        held = self.call("state", "Q001", "--from", "queued", "--to", "deferred")
        self.assertEqual(held["status"], "deferred")
        self.call("state", "Q001", "--from", "deferred", "--to", "queued")
        self.call("claim")
        self.call("attach", "Q001", "--thread", THREAD)
        self.reject("state", "Q001", "--from", "planning", "--to", "queued")
        self.reject("state", "Q001", "--from", "queued", "--to", "done")
        done = self.call("state", "Q001", "--from", "planning", "--to", "done")
        self.assertEqual(done["status"], "done")
        self.assertEqual(done["task"], "Fix the album view")
        self.assertEqual(done["context"], "Source: issue 42")
        self.assertEqual(done["codex_task"], f"codex://threads/{THREAD}")

    def test_malformed_files_are_rejected_before_write(self):
        malformed = [
            EMPTY.replace("<!-- queue:end -->", ""),
            EMPTY + "<!-- queue:start -->",
            EMPTY.replace("| Context |", "| Unknown |"),
            EMPTY.replace("| --- | --- | --- | --- | --- |", "not a separator"),
            EMPTY.replace(TABLE, TABLE + "| Q001 | Title | queued | | | extra |\n"),
            EMPTY.replace(TABLE, TABLE + "| Q001 | Title | mystery | | |\n"),
            EMPTY.replace(TABLE, TABLE + "| Q001 | Title | blocked | invalid | |\n"),
            EMPTY.replace(TABLE, TABLE + "| Q001 | Title | blocked | [Open](codex://threads/no) | |\n"),
            EMPTY.replace(TABLE, TABLE + "| Q001 | Title | queued | | |\n" * 2),
            EMPTY.replace(TABLE, TABLE + "| Q000 | Title | queued | | |\n"),
            EMPTY.replace(TABLE, TABLE + "| Q001 | Title | planning | | |\n"),
            EMPTY.replace(TABLE, TABLE + f"| Q001 | Title | queued | [Open](codex://threads/{THREAD}) | |\n"),
            EMPTY.replace(TABLE, TABLE + f"| Q001 | Title | starting | [Open](codex://threads/{THREAD}) | |\n"),
        ]
        for value in malformed:
            with self.subTest(value=value):
                self.path.write_bytes(value.encode())
                self.reject("add", "--title", "New task", "--context", "Details")

    def test_unknown_task_and_relative_path_are_rejected(self):
        self.reject("state", "Q404", "--from", "queued", "--to", "deferred")
        result = subprocess.run([sys.executable, str(SCRIPT), "--file", "TODO.md", "list"],
                                cwd=self.directory.name, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.path.read_bytes(), EMPTY.encode())

    def test_cancelled_task_keeps_history_but_cannot_be_dispatched_or_resumed(self):
        original = self.add("Abandoned", "Keep the decision", "--thread", THREAD)
        cancelled = self.call("state", "Q001", "--from", "planning", "--to", "cancelled")
        self.assertEqual(cancelled, dict(original, status="cancelled"))
        self.assertEqual(self.call("list"), [])
        self.assertEqual(self.call("list", "--include-cancelled"), [cancelled])
        self.assertIsNone(self.call("claim"))
        self.reject("state", "Q001", "--from", "cancelled", "--to", "implementing")
        self.assertEqual(self.add("New authorized task")["id"], "Q002")

    def test_failed_replace_preserves_file_and_cleans_temporary(self):
        with patch.object(QUEUE.os, "replace", side_effect=OSError("replace failed")):
            with self.assertRaisesRegex(OSError, "replace failed"):
                QUEUE.atomic_write(self.path, "replacement")
        self.assertEqual(self.path.read_bytes(), EMPTY.encode())
        self.assertEqual(list(self.path.parent.iterdir()), [self.path])


if __name__ == "__main__":
    unittest.main()
