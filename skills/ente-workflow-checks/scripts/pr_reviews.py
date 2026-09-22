#!/usr/bin/env python3
"""Collect Ente review evidence or record an evidence-backed disposition locally."""

import argparse
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
from urllib.parse import parse_qs, urlencode, urlsplit
import uuid

AUTHOR = "AmanRajSinghMourya"
REPOS = (AUTHOR + "/ente", "ente-io/ente")
# Verified in the saved sample-pr-52.json, not inferred from a name substring.
BOT = ("chatgpt-codex-connector[bot]", 199175422, "Bot")
THREAD_QUERY = """query($owner:String!,$name:String!,$number:Int!,$cursor:String){
 repository(owner:$owner,name:$name){pullRequest(number:$number){
 reviewThreads(first:100,after:$cursor){nodes{id isResolved isOutdated
 comments(first:1){nodes{databaseId}}}pageInfo{hasNextPage endCursor}}}}} """


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records-root", type=Path, default=Path("/Users/amanraj/development/ente-workflow"))
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--collect", action="store_true", help="Collect GitHub reviews (default)")
    action.add_argument("--record-disposition", type=Path, help="Record one exact revision's assessment from JSON")
    args = parser.parse_args()
    result = record_disposition(args.records_root, args.record_disposition) if args.record_disposition else collect(args.records_root)
    print(json.dumps(result, indent=2))
    return 2 if result["status"] == "incomplete" else 0


def collect(records_root, api=None, now=None):
    """api/time injection is for Python fixtures only, never a CLI option."""
    root = Path(records_root).resolve()
    fetch = Fetch(api or github)
    run = None
    try:
        now = now or datetime.now(timezone.utc)
        started = timestamp(now)
        with review_session(root, now) as held:
            if held:
                return held
            run = root / "raw" / "review-runs" / (now.strftime("%Y%m%dT%H%M%SZ-") + uuid.uuid4().hex)
            run.mkdir(parents=True)
            state_path, ledger_path = root / "review-state.json", root / "review-findings.jsonl"
            state = read_json(state_path) if state_path.exists() else {"version": 1, "prs": []}
            tracked = read_json(root / "tracked-prs.json")
            require(isinstance(state, dict) and isinstance(tracked, dict) and type(state["version"]) is int and
                    type(tracked["version"]) is int and state["version"] == tracked["version"] == 1, "Unsupported records schema")
            require(isinstance(state["prs"], list) and isinstance(tracked["tasks"], list), "PR/task records must be lists")
            old_bytes = ledger_path.read_bytes() if ledger_path.exists() else b""
            old = [json.loads(line) for line in old_bytes.decode("utf-8").splitlines() if line.strip()]
            since = min(now - timedelta(hours=24), instant(state.get("last_success_at", started)))
            targets = {identity(row["repo"], row["number"]) for row in state["prs"]}
            targets.update(identity(row["repo"], row["pr"]) for row in old)
            task_ids = set()
            for task in tracked["tasks"]:
                require(isinstance(task, dict) and isinstance(task["id"], str) and task["id"].strip() and
                        task["id"] not in task_ids, "Task needs a unique nonempty id")
                require(isinstance(task["worktree"], str) and Path(task["worktree"]).is_absolute(), "Task worktree must be absolute")
                require(isinstance(task["prs"], list) and isinstance(task["depends_on"], list) and
                        all(isinstance(item, str) and item.strip() for item in task["depends_on"]), "Invalid task PR/dependency list")
                task_ids.add(task["id"])
                targets.update(identity(row["repo"], row["number"]) for row in task["prs"])
            require(fetch.get("user")["login"] == AUTHOR, "Unexpected GitHub API account")
            query = f"is:pr author:{AUTHOR} " + " ".join("repo:" + repo for repo in REPOS)
            query += " updated:>=" + timestamp(since)
            for item in fetch.pages("search/issues", {"q": query}, search=True):
                require("pull_request" in item and item["user"]["login"] == AUTHOR, "Search identity mismatch")
                repo_url = item["repository_url"]
                require(repo_url.startswith("https://api.github.com/repos/"), "Invalid search repository URL")
                targets.add(identity(repo_url[len("https://api.github.com/repos/"):], item["number"]))
            seen = {revision(row) for row in old}
            additions, snapshots = [], []
            for repo, number in sorted(targets):
                prefix = f"repos/{repo}/pulls/{number}"
                pr = fetch.get(prefix)
                require(pr["number"] == number and pr["user"]["login"] == AUTHOR, "PR author/number mismatch")
                require(identity(pr["base"]["repo"]["full_name"], number) == (repo, number), "PR repository mismatch")
                head = sha(pr["head"]["sha"])
                threads = fetch.threads(repo, number)
                sources = (("review", prefix + "/reviews"), ("inline_comment", prefix + "/comments"),
                           ("issue_comment", f"repos/{repo}/issues/{number}/comments"))
                for kind, endpoint in sources:
                    for item in fetch.pages(endpoint):
                        user = item["user"]
                        require(isinstance(user["login"], str), "Missing comment author")
                        if (user["login"], user["id"], user["type"]) != BOT:
                            continue
                        row = finding(item, kind, repo, number, head, threads, endpoint)
                        row.update(observed_at=started, raw_responses=str(run / "responses.json"))
                        key = revision(row)
                        if key not in seen:
                            additions.append(row)
                            seen.add(key)
                snapshots.append({"repo": repo, "number": number, "head": head,
                                  "observed_at": started, "threads": list(threads.values())})
            raw_path = run / "responses.json"
            atomic(raw_path, json.dumps(fetch.responses, indent=2))
            require((ledger_path.read_bytes() if ledger_path.exists() else b"") == old_bytes,
                    "Review ledger changed during collection; retry without overwriting classifications")
            if additions:
                prefix_bytes = old_bytes + (b"\n" if old_bytes and not old_bytes.endswith(b"\n") else b"")
                atomic(ledger_path, prefix_bytes + "".join(json.dumps(row) + "\n" for row in additions).encode())
            elif not ledger_path.exists():
                atomic(ledger_path, b"")
            pending = [list(revision(row)) for row in old + additions if row["disposition"] == "unverified"]
            result = {"status": "completed", "started_at": started, "since": timestamp(since),
                      "new_count": len(additions), "new_ids": [list(revision(row)) for row in additions],
                      "pending_count": len(pending), "pending_ids": pending,
                      "scopes": [{"repo": repo, "number": number} for repo, number in sorted(targets)],
                      "raw_responses": str(raw_path)}
            atomic(run / "result.json", json.dumps(result, indent=2))
            atomic(state_path, json.dumps({"version": 1, "last_success_at": started, "prs": snapshots}, indent=2))
            return result
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        result = {"status": "incomplete", "error": str(error)}
        if run is not None:
            try:
                atomic(run / "responses.json", json.dumps(fetch.responses, indent=2))
                atomic(run / "result.json", json.dumps(result, indent=2))
            except OSError:
                pass  # The caller still receives incomplete if evidence storage itself failed.
        return result


def record_disposition(records_root, assessment_path, now=None):
    """The only supported classification writer; never infer a judgment here."""
    root = Path(records_root).resolve()
    try:
        now = now or datetime.now(timezone.utc)
        recorded_at = timestamp(now)
        with review_session(root, now) as held:
            if held:
                return held
            assessment = read_json(Path(assessment_path))
            require(isinstance(assessment, dict) and set(assessment) == {"revision", "disposition", "reason", "evidence"},
                    "Assessment needs exactly revision, disposition, reason and evidence")
            key = assessment["revision"]
            require(isinstance(key, list) and len(key) == 5, "Supply an exact five-part revision")
            require(key[0] in REPOS and key[1] in ("review", "inline_comment", "issue_comment") and
                    type(key[2]) is int and key[2] > 0 and isinstance(key[4], str) and
                    re.fullmatch("[0-9a-f]{64}", key[4]), "Invalid revision identity/digest")
            instant(key[3])
            require(assessment["disposition"] in ("unverified", "confirmed", "rejected", "accepted-tradeoff", "fixed"),
                    "Unsupported disposition")
            require(isinstance(assessment["reason"], str) and assessment["reason"].strip(), "Reason must be nonempty")
            evidence = assessment["evidence"]
            require(isinstance(evidence, list) and evidence and all(isinstance(item, str) and item.strip() for item in evidence),
                    "Evidence must be a nonempty list of nonempty strings")
            ledger = root / "review-findings.jsonl"
            lines = ledger.read_bytes().splitlines(keepends=True)
            matches = [(index, json.loads(line)) for index, line in enumerate(lines) if line.strip()]
            matches = [(index, row) for index, row in matches if list(revision(row)) == key]
            require(len(matches) == 1, "Revision must match exactly one existing finding")
            index, row = matches[0]
            history = row.get("assessments", [])
            require(isinstance(history, list), "Existing assessment history must be a list")
            if not history and (row["disposition"] != "unverified" or "reason" in row or "evidence" in row):
                history = [{name: row[name] for name in ("disposition", "reason", "evidence") if name in row}]
            latest = {name: assessment[name] for name in ("disposition", "reason", "evidence")}
            row.update(latest, assessments=history + [dict(latest, recorded_at=recorded_at)])
            ending = b"\r\n" if lines[index].endswith(b"\r\n") else b"\n" if lines[index].endswith(b"\n") else b""
            lines[index] = json.dumps(row).encode("utf-8") + ending
            atomic(ledger, b"".join(lines))
            return {"status": "completed", "revision": key, "disposition": row["disposition"],
                    "assessment_count": len(row["assessments"])}
    except (OSError, ValueError, KeyError, TypeError) as error:
        return {"status": "incomplete", "error": str(error)}


@contextmanager
def review_session(root, now):
    require(not any((parent / ".git").exists() for parent in (root, *root.parents)), "Keep review records outside Git checkouts")
    control = read_json(root / "control.json")
    if now < instant(control["not_before"]):
        yield {"status": "held", "not_before": control["not_before"]}
        return
    with (root / ".review-collection.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield None


class Fetch:
    def __init__(self, api):
        self.api, self.responses = api, []

    def request(self, endpoint, fields=None):
        data, following = self.api(endpoint, fields)
        self.responses.append({"endpoint": endpoint, "fields": fields, "response": data, "next": following})
        return data, following

    def get(self, endpoint):
        data, following = self.request(endpoint)
        require(following is None and isinstance(data, dict), "Unexpected object response")
        return data

    def pages(self, endpoint, params=None, search=False):
        params = dict(params or {}, per_page=100, page=1)
        total, count, seen = None, 0, set()
        while True:
            path = endpoint + "?" + urlencode(params)
            body, following = self.request(path)
            if search:
                require(body["incomplete_results"] is False, "Search was incomplete")
                require(type(body["total_count"]) is int and 0 <= body["total_count"] < 1000, "Search reached its cap")
                require(total in (None, body["total_count"]), "Search changed during pagination")
                total, rows = body["total_count"], body["items"]
            else:
                rows = body
            require(isinstance(rows, list) and (rows or following is None), "Missing collection page")
            for row in rows:
                key = (row["repository_url"], row["number"]) if search else row["id"]
                require(key not in seen, "Repeated item during pagination")
                seen.add(key)
                count += 1
                yield row
            if following is None:
                require(not search or count == total, "Search pages do not match total_count")
                return
            params["page"] += 1
            require(urlsplit(following).path == endpoint and parse_qs(urlsplit(following).query) ==
                    parse_qs(urlencode(params)), "Invalid next-page link")

    def threads(self, repo, number):
        owner, name = repo.split("/")
        result, cursors, cursor = {}, set(), None
        while True:
            fields = {"query": THREAD_QUERY, "owner": owner, "name": name, "number": number, "cursor": cursor}
            body, _ = self.request("graphql", fields)
            require(isinstance(body, dict) and not body.get("errors"), "GraphQL returned errors/invalid data")
            connection = body["data"]["repository"]["pullRequest"]["reviewThreads"]
            require(isinstance(connection["nodes"], list), "Missing review threads")
            for thread in connection["nodes"]:
                first = thread["comments"]["nodes"]
                require(len(first) == 1 and type(first[0]["databaseId"]) is int, "Missing thread root")
                root_id = first[0]["databaseId"]
                require(root_id not in result and isinstance(thread["id"], str), "Duplicate/invalid thread")
                require(type(thread["isResolved"]) is bool and type(thread["isOutdated"]) is bool, "Missing thread state")
                result[root_id] = {"id": thread["id"], "root_comment_id": root_id,
                                   "resolved": thread["isResolved"], "outdated": thread["isOutdated"]}
            page = connection["pageInfo"]
            require(type(page["hasNextPage"]) is bool, "Missing thread pagination")
            if not page["hasNextPage"]:
                return result
            cursor = page["endCursor"]
            require(isinstance(cursor, str) and cursor and cursor not in cursors and connection["nodes"], "Missing/repeated thread cursor")
            cursors.add(cursor)


def finding(item, kind, repo, number, head, threads, endpoint):
    require(type(item["id"]) is int and isinstance(item["body"], str), "Invalid review identity/body")
    updated = item["submitted_at"] if kind == "review" else item["updated_at"]
    instant(updated)
    url = item["html_url"]
    require(isinstance(url, str) and urlsplit(url)._replace(fragment="").geturl() ==
            f"https://github.com/{repo}/pull/{number}", "Invalid review URL")
    reviewed = None if kind == "issue_comment" else sha(item["commit_id"])
    row = {"repo": repo, "pr": number, "kind": kind, "id": item["id"], "updated_at": updated,
           "url": url, "reviewed_sha": reviewed, "original_sha": sha(item["original_commit_id"]) if kind == "inline_comment" else reviewed,
           "current_head": head, "claim": item["body"], "author": {key: item["user"][key] for key in ("login", "id", "type")}, "source": endpoint,
           "disposition": "unverified"}
    if kind == "review":
        require(item["state"] in ("COMMENTED", "APPROVED", "CHANGES_REQUESTED", "DISMISSED", "PENDING"), "Invalid review state")
        row["state"] = item["state"]
    if kind == "inline_comment":
        row["thread"] = threads.get(item.get("in_reply_to_id", item["id"]))
        require(row["thread"] is not None, "Inline comment missing its review thread")
    return row


def revision(row):
    identity(row["repo"], row["pr"])
    content = json.dumps([row["claim"], row.get("state")], separators=(",", ":"))
    return row["repo"], row["kind"], row["id"], row["updated_at"], hashlib.sha256(content.encode()).hexdigest()


def github(endpoint, fields=None):
    command = ["gh", "api", "--hostname", "github.com", "--include"]
    if fields is None:
        command += ["--method", "GET", endpoint]
        payload = None
    else:
        command += ["graphql", "--input", "-"]
        payload = json.dumps({"query": fields["query"], "variables": {key: value for key, value in fields.items() if key != "query"}})
    response = subprocess.run(command, input=payload, text=True, capture_output=True, check=True, timeout=60)
    headers, separator, body = response.stdout.replace("\r\n", "\n").partition("\n\n")
    require(separator and re.match(r"HTTP/\S+ 200\b", headers), "Missing successful API response headers")
    link = re.search(r'<([^>]+)>;\s*rel="next"', headers)
    following = None
    if link:
        parsed = urlsplit(link[1])
        require(parsed.scheme == "https" and parsed.netloc == "api.github.com", "Unexpected pagination host")
        following = parsed.path.lstrip("/") + "?" + parsed.query
    return json.loads(body), following


def identity(repo, number):
    require(repo in REPOS and type(number) is int and number > 0, "Unsupported repository/PR identity")
    return repo, number


def sha(value):
    require(isinstance(value, str) and re.fullmatch("[0-9a-f]{40}", value), "Missing full commit SHA")
    return value


def instant(value):
    require(isinstance(value, str), "Missing timestamp")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    require(parsed.utcoffset() is not None, "Timestamp needs a timezone")
    return parsed


def timestamp(value):
    require(value.utcoffset() is not None, "Timestamp needs a timezone")
    return value.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def atomic(path, content):
    data = content.encode("utf-8") if isinstance(content, str) else content
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix="." + path.name, delete=False) as output:
        temporary = Path(output.name)
        try:
            output.write(data)
            output.flush()
            os.fsync(output.fileno())
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)


def require(condition, message):
    if not condition:
        raise ValueError(message)


if __name__ == "__main__":
    raise SystemExit(main())
