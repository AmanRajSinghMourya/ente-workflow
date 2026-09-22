#!/usr/bin/env python3
"""Offline acceptance fixtures for the Ente review collector."""

import copy
from datetime import datetime, timezone
import fcntl
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

sys.dont_write_bytecode = True
import pr_reviews

REPO = "AmanRajSinghMourya/ente"
NOW = datetime(2026, 9, 21, 12, tzinfo=timezone.utc)
STAMP = "2026-09-21T11:00:00Z"
HEAD = "a" * 40
OLD = "b" * 40
BOT = {"login": "chatgpt-codex-connector[bot]", "id": 199175422, "type": "Bot"}


def comment(number=1, kind="inline_comment"):
    value = {"id": number, "body": "Preserve the old value", "user": BOT,
             "html_url": f"https://github.com/{REPO}/pull/52#discussion_r{number}",
             "updated_at": STAMP, "created_at": STAMP}
    if kind == "inline_comment":
        value.update(commit_id=OLD, original_commit_id=OLD)
    if kind == "review":
        value.update(commit_id=OLD, state="COMMENTED", submitted_at=STAMP)
    return value


class FixtureAPI:
    def __init__(self):
        self.calls = []
        self.login = "AmanRajSinghMourya"
        self.author = self.login
        self.repo = REPO
        self.head = HEAD
        self.search = [52]
        self.search_count = None
        self.incomplete_search = False
        self.fail = None
        self.inline = [comment()]
        self.reviews = [comment(2, "review")]
        self.issues = [comment(3, "issue_comment")]
        self.threads = [{"id": "T1", "isResolved": False, "isOutdated": True,
                         "comments": {"nodes": [{"databaseId": 1}]}}]
        self.page_size = 1

    def __call__(self, endpoint, fields=None):
        self.calls.append((endpoint, fields))
        if self.fail and self.fail in endpoint:
            raise ValueError("fixture API failure")
        if endpoint == "user":
            return {"login": self.login}, None
        if endpoint == "graphql":
            index = int(fields.get("cursor") or 0)
            nodes = copy.deepcopy(self.threads[index:index + self.page_size])
            for node in nodes:
                for first in node["comments"]["nodes"]:
                    first["databaseId"] += (fields["number"] - 52) * 1000
            end = index + len(nodes)
            return {"data": {"repository": {"pullRequest": {"reviewThreads": {
                "nodes": nodes, "pageInfo": {"hasNextPage": end < len(self.threads),
                                             "endCursor": str(end)}}}}}}, None
        path = urlsplit(endpoint).path
        query = parse_qs(urlsplit(endpoint).query)
        page = int(query.get("page", [1])[0])
        if path == "search/issues":
            values = [{"number": n, "repository_url": "https://api.github.com/repos/" + REPO,
                       "user": {"login": self.author}, "pull_request": {}} for n in self.search]
        elif path.endswith("/reviews"):
            values = self.reviews
        elif "/pulls/" in path and path.endswith("/comments"):
            values = self.inline
        elif "/issues/" in path and path.endswith("/comments"):
            values = self.issues
        else:
            return {"number": int(path.rsplit("/", 1)[1]), "user": {"login": self.author},
                    "base": {"repo": {"full_name": self.repo}}, "head": {"sha": self.head}}, None
        start = (page - 1) * self.page_size
        body = copy.deepcopy(values[start:start + self.page_size])
        if path != "search/issues":
            pr = int(path.split("/")[-2])
            for item in body:
                item["id"] += (pr - 52) * 1000
                item["html_url"] = item["html_url"].replace("/pull/52#", f"/pull/{pr}#")
        following = endpoint.rsplit("page=", 1)[0] + "page=" + str(page + 1) if start + self.page_size < len(values) else None
        if path == "search/issues":
            body = {"items": body, "total_count": self.search_count if self.search_count is not None else len(values),
                    "incomplete_results": self.incomplete_search}
        return body, following


class ReviewCollectorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.api = FixtureAPI()
        self.tracked = {"version": 1, "tasks": []}
        self.write("tracked-prs.json", self.tracked)
        self.write("control.json", {"not_before": "2026-09-20T12:00:00Z", "cleanup_mode": "audit"})

    def tearDown(self):
        self.temp.cleanup()

    def write(self, name, value):
        (self.root / name).write_text(json.dumps(value) + "\n")

    def run_collection(self):
        return pr_reviews.collect(self.root, api=self.api, now=NOW)

    def findings(self):
        return [json.loads(line) for line in (self.root / "review-findings.jsonl").read_text().splitlines()]

    def test_complete_records_bot_identity_sources_and_stale_review_sha(self):
        result = self.run_collection()
        self.assertEqual(result["status"], "completed", result)
        rows = self.findings()
        self.assertEqual(len(rows), 3)
        inline = next(row for row in rows if row["kind"] == "inline_comment")
        self.assertEqual((inline["reviewed_sha"], inline["current_head"]), (OLD, HEAD))
        self.assertEqual(inline["thread"]["id"], "T1")
        self.assertIsNone(next(row for row in rows if row["kind"] == "issue_comment")["reviewed_sha"])
        self.assertTrue(all(row["disposition"] == "unverified" for row in rows))
        self.assertTrue(Path(result["raw_responses"]).exists())
        self.assertEqual(json.loads((self.root / "tracked-prs.json").read_text()), self.tracked)

    def test_paginates_every_rest_collection_and_threads(self):
        self.api.search = [52, 53]
        self.api.inline.append(comment(4))
        self.api.reviews.append(comment(5, "review"))
        self.api.issues.append(comment(6, "issue_comment"))
        self.api.threads.append({"id": "T2", "isResolved": True, "isOutdated": False,
                                 "comments": {"nodes": [{"databaseId": 4}]}})
        result = self.run_collection()
        self.assertEqual(result["status"], "completed", result)
        self.assertEqual(len(self.findings()), 12)
        self.assertTrue(any(endpoint == "graphql" and fields.get("cursor") == "1" for endpoint, fields in self.api.calls))

    def test_duplicate_runs_and_head_changes_preserve_human_disposition(self):
        self.run_collection()
        rows = self.findings()
        rows[0]["disposition"] = "rejected"
        raw = "".join(json.dumps(row) + "\n" for row in rows)
        (self.root / "review-findings.jsonl").write_text(raw)
        self.api.head = "c" * 40
        result = self.run_collection()
        self.assertEqual(result["new_count"], 0)
        self.assertEqual((self.root / "review-findings.jsonl").read_text(), raw)
        state = json.loads((self.root / "review-state.json").read_text())
        self.assertEqual(state["prs"][0]["head"], "c" * 40)

    def test_edit_with_same_timestamp_preserves_both_revisions(self):
        self.run_collection()
        self.api.inline[0]["body"] = "Edited finding"
        result = self.run_collection()
        self.assertEqual(result["new_count"], 1)
        self.assertEqual(len(self.findings()), 4)

    def test_legacy_sample_is_preserved_without_duplicate(self):
        row = {"repo": REPO, "pr": 52, "kind": "inline_comment", "id": 1, "updated_at": STAMP,
               "claim": self.api.inline[0]["body"], "disposition": "confirmed"}
        raw = json.dumps(row) + "\n"
        (self.root / "review-findings.jsonl").write_text(raw)
        self.assertEqual(self.run_collection()["new_count"], 2)
        self.assertTrue((self.root / "review-findings.jsonl").read_text().startswith(raw))

    def test_tracked_and_observed_prs_revisited_without_recent_search_match(self):
        self.run_collection()
        self.api.search = []
        task = {"id": "B-photos-late-review", "worktree": "/tmp/B-photos-late-review", "depends_on": [],
                "prs": [{"repo": REPO, "number": 71}]}
        self.write("tracked-prs.json", {"version": 1, "tasks": [task]})
        self.api.calls.clear()
        self.assertEqual(self.run_collection()["status"], "completed")
        endpoints = [call[0] for call in self.api.calls]
        self.assertIn("repos/" + REPO + "/pulls/52", endpoints)
        self.assertIn("repos/" + REPO + "/pulls/71", endpoints)

    def test_watermark_covers_gap_since_last_success(self):
        self.write("review-state.json", {"version": 1, "last_success_at": "2026-09-17T12:00:00Z", "prs": []})
        self.run_collection()
        query = next(parse_qs(urlsplit(path).query)["q"][0] for path, _ in self.api.calls if path.startswith("search/"))
        self.assertIn("updated:>=2026-09-17T12:00:00Z", query)

    def assert_invalid_records(self, tracked=None, state=None):
        self.api.search = []
        self.api.calls.clear()
        self.write("tracked-prs.json", tracked)
        self.write("review-state.json", state)
        previous = (self.root / "review-state.json").read_bytes()
        self.assertEqual(self.run_collection()["status"], "incomplete")
        self.assertEqual(self.api.calls, [], "Invalid records must fail before authenticating or querying GitHub")
        self.assertEqual((self.root / "review-state.json").read_bytes(), previous)

    def test_malformed_record_containers_fail_before_api_and_watermark(self):
        state = {"version": 1, "last_success_at": "2026-09-17T12:00:00Z", "prs": []}
        for tasks in ({}, None, "empty"):
            with self.subTest(tasks=tasks):
                self.assert_invalid_records({"version": 1, "tasks": tasks}, state)
        for prs in ({}, None):
            with self.subTest(task_prs=prs):
                task = {"id": "B-photos-fixture", "worktree": "/tmp/B-photos-fixture", "depends_on": [], "prs": prs}
                self.assert_invalid_records({"version": 1, "tasks": [task]}, state)
        for malformed in ({"version": 1, "prs": {}}, [], None, "empty", {"version": 2, "prs": []}):
            with self.subTest(state=malformed):
                self.assert_invalid_records(self.tracked, malformed)
        for malformed in ([], None, "empty", {"version": 2, "tasks": []}):
            with self.subTest(tracked=malformed):
                self.assert_invalid_records(malformed, state)

    def test_invalid_task_identity_and_dependencies_fail_before_api(self):
        state = {"version": 1, "last_success_at": "2026-09-17T12:00:00Z", "prs": []}
        task = {"id": "B-photos-fixture", "worktree": "/tmp/B-photos-fixture", "depends_on": [], "prs": []}
        for missing in ("id", "worktree", "depends_on"):
            with self.subTest(missing=missing):
                self.assert_invalid_records({"version": 1, "tasks": [{key: value for key, value in task.items() if key != missing}]}, state)
        for field, value in (("id", " "), ("worktree", "relative/path"), ("worktree", None),
                             ("depends_on", {}), ("depends_on", [""]), ("depends_on", [42])):
            with self.subTest(field=field, value=value):
                self.assert_invalid_records({"version": 1, "tasks": [dict(task, **{field: value})]}, state)
        self.assert_invalid_records({"version": 1, "tasks": [None]}, state)

    def test_duplicate_task_ids_fail_before_api(self):
        state = {"version": 1, "last_success_at": "2026-09-17T12:00:00Z", "prs": []}
        task = {"id": "B-photos-fixture", "worktree": "/tmp/B-photos-fixture", "depends_on": [], "prs": []}
        self.assert_invalid_records({"version": 1, "tasks": [task, dict(task, worktree="/tmp/other-task")]}, state)

    def test_failure_preserves_ledger_and_success_watermark(self):
        self.run_collection()
        previous = {name: (self.root / name).read_bytes() for name in ("review-findings.jsonl", "review-state.json")}
        self.api.inline[0]["body"] = "Do not persist partial collection"
        self.api.fail = "/reviews"
        self.assertEqual(self.run_collection()["status"], "incomplete")
        for name, content in previous.items():
            self.assertEqual((self.root / name).read_bytes(), content)

    def test_unknown_search_and_identity_fail_closed(self):
        for field, value in [("incomplete_search", True), ("search_count", 1000), ("search_count", 3),
                             ("login", "other"), ("author", "other"), ("repo", "other/ente")]:
            with self.subTest(field=field):
                self.api = FixtureAPI()
                setattr(self.api, field, value)
                self.assertEqual(self.run_collection()["status"], "incomplete")

    def test_missing_fields_and_graphql_errors_fail_closed(self):
        del self.api.inline[0]["commit_id"]
        self.assertEqual(self.run_collection()["status"], "incomplete")
        self.api = FixtureAPI()
        self.api.threads[0]["comments"]["nodes"] = []
        self.assertEqual(self.run_collection()["status"], "incomplete")
        api = self.api
        self.api = lambda path, fields=None: ({"errors": [{"message": "fixture"}]}, None) if path == "graphql" else api(path, fields)
        self.assertEqual(self.run_collection()["status"], "incomplete")

    def test_unverified_similar_bot_login_is_not_collected(self):
        self.api.inline[0]["user"] = {"login": "fake-codex[bot]", "id": 42, "type": "Bot"}
        self.assertEqual(self.run_collection()["new_count"], 2)

    def test_hold_runs_before_any_api_call_and_missing_control_cannot_bypass_it(self):
        self.write("control.json", {"not_before": "2026-09-23T12:30:00Z"})
        self.assertEqual(self.run_collection()["status"], "held")
        self.assertEqual(self.api.calls, [])
        (self.root / "control.json").unlink()
        self.assertEqual(self.run_collection()["status"], "incomplete")
        self.assertEqual(self.api.calls, [])

    def test_lock_blocks_concurrent_job_before_api_calls(self):
        with (self.root / ".review-collection.lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.assertEqual(self.run_collection()["status"], "incomplete")
            self.assertEqual(self.api.calls, [])

    def test_issue_comments_have_no_invented_commit_and_replies_use_root_thread(self):
        reply = comment(4)
        reply["in_reply_to_id"] = 1
        self.api.inline.append(reply)
        self.assertEqual(self.run_collection()["status"], "completed")
        self.assertEqual(next(row for row in self.findings() if row["id"] == 4)["thread"]["id"], "T1")

    def test_full_run_evidence_failure_does_not_advance_watermark(self):
        self.run_collection()
        old = (self.root / "review-state.json").read_bytes()
        real_atomic = pr_reviews.atomic

        def fail_result(path, content):
            if path.name == "result.json":
                raise OSError("fixture write failure")
            return real_atomic(path, content)

        with patch.object(pr_reviews, "atomic", fail_result):
            self.assertEqual(self.run_collection()["status"], "incomplete")
        self.assertEqual((self.root / "review-state.json").read_bytes(), old)

    def test_cli_hold_and_missing_control_exit_codes_without_network(self):
        self.write("control.json", {"not_before": "2999-01-01T00:00:00Z"})
        command = [sys.executable, "-B", str(Path(pr_reviews.__file__)), "--records-root", str(self.root)]
        result = subprocess.run(command, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)["status"], "held")
        (self.root / "control.json").unlink()
        result = subprocess.run(command, text=True, capture_output=True)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stdout)["status"], "incomplete")

    def test_gh_adapter_uses_explicit_host_and_parses_headers_and_graphql_variables(self):
        response = SimpleNamespace(stdout='HTTP/2.0 200 OK\nLink: <https://api.github.com/repos/o/r/pulls?page=2>; rel="next"\n\n[]')
        with patch.object(pr_reviews.subprocess, "run", return_value=response) as run:
            body, following = pr_reviews.github("repos/o/r/pulls")
            self.assertEqual((body, following), ([], "repos/o/r/pulls?page=2"))
            self.assertEqual(run.call_args[0][0][:5], ["gh", "api", "--hostname", "github.com", "--include"])
            pr_reviews.github("graphql", {"query": "query{}", "number": 52, "cursor": None})
            self.assertEqual(json.loads(run.call_args[1]["input"])["variables"], {"number": 52, "cursor": None})

    def test_second_page_failure_and_wrong_next_path_are_incomplete(self):
        self.api.inline.append(comment(4))
        self.api.fail = "/comments?per_page=100&page=2"
        self.assertEqual(self.run_collection()["status"], "incomplete")
        api = FixtureAPI()

        def wrong_path(path, fields=None):
            data, following = api(path, fields)
            return (data, "repos/other/ente/pulls?per_page=100&page=2") if "/reviews?" in path else (data, following)

        self.api = wrong_path
        self.assertEqual(self.run_collection()["status"], "incomplete")

    def assessment(self, row=None, **changes):
        row = row or self.findings()[0]
        result = {"revision": list(pr_reviews.revision(row)), "disposition": "confirmed",
                  "reason": "Reproduced the original behavior", "evidence": ["evidence/reproduction.txt"]}
        result.update(changes)
        self.write("assessment.json", result)
        return self.root / "assessment.json"

    def classify(self, path):
        self.assertTrue(callable(getattr(pr_reviews, "record_disposition", None)),
                        "A supported classification writer must share the collector lock")
        return pr_reviews.record_disposition(self.root, path, now=NOW)

    def test_classifier_preserves_evidence_and_append_only_assessments_across_collection(self):
        self.run_collection()
        original = self.findings()[0]
        first = self.classify(self.assessment())
        self.assertEqual(first["status"], "completed", first)
        previous = self.findings()[0]["assessments"]
        second = self.classify(self.assessment(disposition="fixed", reason="Regression test now passes"))
        self.assertEqual(second["status"], "completed", second)
        classified = self.findings()[0]
        classification_keys = {"disposition", "reason", "evidence", "assessments"}
        self.assertEqual({key: value for key, value in classified.items() if key not in classification_keys},
                         {key: value for key, value in original.items() if key not in classification_keys})
        self.assertEqual(classified["assessments"][:-1], previous)
        self.assertEqual(classified["assessments"][-1]["disposition"], "fixed")
        self.assertEqual(classified["reason"], "Regression test now passes")
        before = (self.root / "review-findings.jsonl").read_bytes()
        result = self.run_collection()
        self.assertEqual((self.root / "review-findings.jsonl").read_bytes(), before)
        self.assertEqual(result["pending_count"], 2)
        self.assertNotIn(list(pr_reviews.revision(original)), result["pending_ids"])

    def test_classifier_cannot_succeed_between_collector_compare_and_replace(self):
        self.run_collection()
        assessment = self.assessment()
        self.api.inline[0]["body"] = "New finding forces a ledger replacement"
        real_atomic, overlapping = pr_reviews.atomic, []

        def overlap(path, content):
            if path.name == "review-findings.jsonl":
                overlapping.append(self.classify(assessment))
            return real_atomic(path, content)

        with patch.object(pr_reviews, "atomic", overlap):
            self.assertEqual(self.run_collection()["status"], "completed")
        self.assertEqual([result["status"] for result in overlapping], ["incomplete"])
        self.assertEqual(self.classify(assessment)["status"], "completed")
        self.assertEqual(self.findings()[0]["disposition"], "confirmed")
        self.assertEqual(len(self.findings()), 4)

    def test_collector_cannot_succeed_during_classifier_replace(self):
        self.run_collection()
        assessment = self.assessment()
        self.api.calls.clear()
        real_atomic, overlapping = pr_reviews.atomic, []

        def overlap(path, content):
            if path.name == "review-findings.jsonl":
                overlapping.append(self.run_collection())
            return real_atomic(path, content)

        with patch.object(pr_reviews, "atomic", overlap):
            self.assertEqual(self.classify(assessment)["status"], "completed")
        self.assertEqual([result["status"] for result in overlapping], ["incomplete"])
        self.assertEqual(self.api.calls, [])
        self.assertEqual(self.run_collection()["pending_count"], 2)

    def test_retry_reports_pending_after_new_revision_persisted_but_run_failed(self):
        self.run_collection()
        for failure in ("result.json", "review-state.json"):
            with self.subTest(failure=failure):
                self.api.inline[0]["body"] = "New revision before failure in " + failure
                real_atomic = pr_reviews.atomic

                def fail_later(path, content):
                    if path.name == failure:
                        raise OSError("fixture failure after ledger saved")
                    return real_atomic(path, content)

                with patch.object(pr_reviews, "atomic", fail_later):
                    self.assertEqual(self.run_collection()["status"], "incomplete")
                persisted = self.findings()
                result = self.run_collection()
                self.assertEqual(result["new_count"], 0)
                self.assertIn("pending_ids", result, "Persisted findings still need triage after a failed run")
                self.assertEqual(result["pending_count"], len(persisted))
                self.assertEqual(result["pending_ids"], [list(pr_reviews.revision(row)) for row in persisted])

    def test_classifier_rejects_invalid_assessment_without_ledger_mutation(self):
        self.run_collection()
        before = (self.root / "review-findings.jsonl").read_bytes()
        invalid = ({"revision": []}, {"revision": [REPO, "review", 99999, STAMP, "a" * 64]},
                   {"disposition": "approved"}, {"reason": "  "}, {"evidence": []},
                   {"evidence": [""]}, {"evidence": "not a list"}, {"claim": "Changed claim"})
        for changes in invalid:
            with self.subTest(changes=changes):
                self.assertEqual(self.classify(self.assessment(**changes))["status"], "incomplete")
                self.assertEqual((self.root / "review-findings.jsonl").read_bytes(), before)
        self.write("assessment.json", {"disposition": "confirmed"})
        self.assertEqual(self.classify(self.root / "assessment.json")["status"], "incomplete")
        self.assertEqual((self.root / "review-findings.jsonl").read_bytes(), before)

    def test_classifier_requires_exactly_one_existing_revision(self):
        self.run_collection()
        assessment = self.assessment()
        ledger = self.root / "review-findings.jsonl"
        ledger.write_bytes(ledger.read_bytes() + (json.dumps(self.findings()[0]) + "\n").encode())
        before = ledger.read_bytes()
        self.assertEqual(self.classify(assessment)["status"], "incomplete")
        self.assertEqual(ledger.read_bytes(), before)

    def test_classifier_hold_has_no_mutation_and_cli_action_is_exclusive(self):
        self.run_collection()
        assessment = self.assessment()
        self.write("control.json", {"not_before": "2999-01-01T00:00:00Z"})
        before = (self.root / "review-findings.jsonl").read_bytes()
        self.assertEqual(self.classify(assessment)["status"], "held")
        command = [sys.executable, "-B", str(Path(pr_reviews.__file__)), "--records-root", str(self.root),
                   "--record-disposition", str(assessment)]
        held = subprocess.run(command, text=True, capture_output=True)
        self.assertEqual(held.returncode, 0, held.stderr)
        self.assertEqual(json.loads(held.stdout)["status"], "held")
        conflicting = subprocess.run(command + ["--collect"], text=True, capture_output=True)
        self.assertEqual(conflicting.returncode, 2)
        self.assertEqual((self.root / "review-findings.jsonl").read_bytes(), before)

    def test_classifier_preserves_legacy_assessment_when_starting_history(self):
        self.run_collection()
        rows = self.findings()
        rows[0].update(disposition="rejected", reason="Previous human judgment", evidence=["older-evidence.md"])
        (self.root / "review-findings.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows))
        self.assertEqual(self.classify(self.assessment())["status"], "completed")
        history = self.findings()[0]["assessments"]
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0], {key: rows[0][key] for key in ("disposition", "reason", "evidence")})
        self.assertEqual(history[1]["disposition"], "confirmed")


if __name__ == "__main__":
    unittest.main()
