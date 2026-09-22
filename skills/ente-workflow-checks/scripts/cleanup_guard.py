#!/usr/bin/env python3
"""Read-only cleanup eligibility audit. Never closes a PR or deletes anything.

Eligibility is a snapshot, not mutation authorization. Fresh complete Codex app
activity evidence must be supplied externally; this script cannot prove global
app idleness. Keep automation audit-only until a live dry-run after the hold.
Python 3.9+, stdlib; API and clock are injectable for offline replay.
"""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

AUTHOR = "AmanRajSinghMourya"
FORK, UPSTREAM = AUTHOR + "/ente", "ente-io/ente"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--records-root", type=Path, required=True)
    parser.add_argument("--activity-evidence", type=Path)
    args = parser.parse_args()
    result = audit(args.repo, args.records_root, args.activity_evidence)
    print(json.dumps(result, indent=2))
    return 2 if result["status"] == "incomplete" else 0


def audit(repo, records, activity=None, api=None, now=None):
    """Audit recorded tasks using GET-only API calls after the hold is over."""
    api = api or github
    clock = (lambda: now) if now is not None else (lambda: datetime.now(timezone.utc))
    results = []
    try:
        repo, records = Path(repo), Path(records)
        control_bytes = (records / "control.json").read_bytes()
        control = json.loads(control_bytes)
        not_before = utc(control["not_before"])
        require(control["cleanup_mode"] == "audit", "Cleanup mode must remain audit-only")
        if clock() < not_before:
            return {"status": "held", "not_before": not_before.isoformat(), "tasks": [], "mutation_authorized": False}
        require(repo.is_absolute() and records.is_absolute(), "Absolute repository and records paths required")
        require(not symlink_path(repo) and not symlink_path(records), "Root path contains a symlink")
        repo, records = repo.resolve(strict=True), records.resolve(strict=True)
        require(Path(git(repo, "rev-parse", "--show-toplevel").strip()).resolve() == repo, "--repo must be the exact main checkout")
        registry = worktrees(repo)
        require(registry and Path(registry[0]["worktree"]).resolve() == repo, "--repo is not the main checkout")
        require(all(not beneath(records, Path(row["worktree"]).resolve()) for row in registry), "Records must be outside every checkout")
        ledger_bytes = (records / "tracked-prs.json").read_bytes()
        ledger = json.loads(ledger_bytes)
        require(ledger["version"] == 1 and isinstance(ledger["tasks"], list), "Malformed task ledger")
        tasks = ledger["tasks"]
        require(all(isinstance(t, dict) and isinstance(t.get("id"), str) and isinstance(t.get("worktree"), str)
                    and isinstance(t.get("depends_on"), list) for t in tasks), "Incomplete global task/dependency ledger")
        require(len({t["id"] for t in tasks}) == len(tasks), "Duplicate task identifiers")
        if isinstance(activity, Path):
            activity = json.loads(activity.read_bytes())
        for task in tasks:
            result = {"id": task["id"], "status": "unknown", "reasons": [], "evidence": {}, "proposed_actions": [], "mutation_authorized": False}
            try:
                result.update(check_task(repo, records, task, tasks, registry, activity, api, clock))
            except (GuardIssue, OSError, ValueError, TypeError, KeyError, AttributeError, subprocess.SubprocessError) as error:
                result.update(status=getattr(error, "status", "unknown"), reasons=[str(error)])
            results.append(result)
        require(control_bytes == (records / "control.json").read_bytes() and ledger_bytes == (records / "tracked-prs.json").read_bytes(), "Control or task ledger changed during audit")
        require(registry == worktrees(repo), "Worktree registration changed during audit")
        return {"status": "incomplete" if any(r["status"] == "unknown" for r in results) else "complete", "tasks": results, "mutation_authorized": False}
    except (GuardIssue, OSError, ValueError, TypeError, KeyError, AttributeError, subprocess.SubprocessError) as error:
        for result in results:
            result.update(status="unknown", reasons=[str(error)], proposed_actions=[])
        return {"status": "incomplete", "reasons": [str(error)], "tasks": results, "mutation_authorized": False}


def check_task(repo, records, task, tasks, registry, activity, api, clock):
    require(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,127}", task["id"]), "Invalid task ID")
    target = Path(task["worktree"])
    require(target.is_absolute() and not symlink_path(target), "Worktree path is relative or symlinked")
    target = target.resolve(strict=True)
    require(target != repo and target != records and target != repo / ".worktrees" and beneath(target, repo / ".worktrees"), "Protected or outside worktree target", "blocked")
    rows = [r for r in registry if Path(r["worktree"]).resolve() == target]
    require(len(rows) == 1, "Target is not exactly one registered worktree")
    row = rows[0]
    require(not any(key in row for key in ("locked", "prunable", "detached", "bare")), "Worktree is locked, prunable, detached or bare", "blocked")
    branch, head = task["branch"], task["head_sha"]
    require(isinstance(branch, str) and branch.startswith("aman/") and sha(head), "Invalid expected branch or commit")
    require(task["status"] == "completed", "Task is not explicitly completed", "blocked")
    require(row.get("branch") == "refs/heads/" + branch and row.get("HEAD") == head, "Registered branch or HEAD differs from mapping", "blocked")
    for other in tasks:
        if other["id"] != task["id"]:
            require(Path(other["worktree"]).resolve() != target, "Worktree is shared by another task", "blocked")
            require(task["id"] not in other["depends_on"] or other.get("status") == "completed", "An unfinished task depends on this slice", "blocked")
    completed = {t["id"] for t in tasks if t.get("status") == "completed"}
    require(all(dep in completed for dep in task["depends_on"]), "Task has unresolved dependencies", "blocked")
    before = snapshot(target)
    require(before["head"].strip() == head and before["branch"].strip() == "refs/heads/" + branch, "Checkout branch or HEAD differs from mapping", "blocked")
    require(all(record.startswith("H ") for record in before["flags"].split("\0") if record), "Hidden index flags or unresolved entries", "blocked")
    require(not any(record.startswith("160000 ") for record in before["index"].split("\0")), "Submodules require separate preservation", "blocked")
    require(not before["operations"], "Git operation or lock is in progress", "blocked")
    archive, manifest = check_archive(records, target, task, head)
    task_link = target / ".task"
    require(task_link.is_symlink() and task_link.resolve(strict=True) == archive, ".task must be one symlink to the verified archive directory", "blocked")
    for entry in before["status"].split("\0"):
        if entry:
            require(entry[:3] in ("!! ", "?? ") and entry[3:] == ".task", "Worktree contains tracked, staged, untracked or ignored changes: " + repr(entry), "blocked")
    check_activity(activity, task, target, clock())
    require(isinstance(task["mapping_evidence"], str) and task["mapping_evidence"].strip(), "PR pairing evidence is missing")
    pairs = [task["fork"], task["upstream"]]
    require(pairs[0]["head_repo"] == FORK and pairs[0]["head_branch"] == branch, "Fork head does not match the local branch")
    require(isinstance(task["prs"], list) and len(task["prs"]) == 2 and
            {(p["repo"], p["number"]) for p in task["prs"]} == {(FORK, pairs[0]["number"]), (UPSTREAM, pairs[1]["number"])}, "PR list does not match the exact fork/upstream pair")
    first = refresh_prs(api, pairs, head)
    require(first["upstream"]["merged"] is True and first["upstream"]["merged_at"] and first["upstream"]["state"] == "closed", "Upstream PR is not merged; closed-unmerged tasks need a decision", "blocked")
    second = refresh_prs(api, pairs, head)
    require(first == second, "PR state or identity changed during audit")
    require((archive, manifest) == check_archive(records, target, task, head, restore=False), "Archive changed during audit")
    require(not symlink_path(target) and task_link.is_symlink() and task_link.resolve(strict=True) == archive, "Worktree or task link changed during audit")
    check_activity(activity, task, target, clock())
    require(before == snapshot(target), "Git state changed during audit")
    actions = []
    if first["fork"]["state"] == "open":
        actions.append({"action": "close_fork_pr", "repo": FORK, "number": pairs[0]["number"], "expected_head": head})
    actions.extend([{"action": "remove_worktree", "path": str(target), "expected_head": head},
                    {"action": "delete_local_branch", "repo": str(repo), "branch": branch, "expected_head": head}])
    return {"status": "eligible", "reasons": ["All audit checks passed; fresh revalidation and separate execution authorization are still required"],
            "evidence": {"worktree": str(target), "branch": branch, "head_sha": head, "archive": str(archive), "manifest": manifest,
                         "mapping_evidence": task["mapping_evidence"], "prs": first, "activity_captured_at": activity["captured_at"]}, "proposed_actions": actions}


def check_archive(records, target, task, head, restore=True):
    value = task["archive"]
    archive = Path(value["path"])
    require(archive.is_absolute() and not symlink_path(archive) and archive.is_dir(), "Archive is missing or symlinked")
    archive = archive.resolve(strict=True)
    require(beneath(archive, records / "tasks" / task["id"]) and not beneath(archive, target), "Archive is outside its task record directory")
    require(isinstance(value["files"], list) and value["files"], "Archive manifest is empty")
    manifest = {}
    bundles = []
    for entry in value["files"]:
        name = entry["path"]
        relative = Path(name)
        require(isinstance(name, str) and not relative.is_absolute() and ".." not in relative.parts and name not in manifest, "Invalid or duplicate manifest path")
        path = archive / relative
        require(path.is_file() and not symlink_path(path) and beneath(path.resolve(), archive), "Archive file missing, symlinked or escaped: " + name)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        require(digest == entry["sha256"], "Archive hash mismatch: " + name)
        manifest[name] = digest
        if name.endswith(".bundle"):
            git(target, "bundle", "verify", str(path))
            with path.open("rb") as handle:
                for line in handle:
                    require(not line.startswith(b"-"), "Bundle requires history outside the archive")
                    if line in (b"\n", b"\r\n"):
                        break
            if any(line.split(" ", 1)[0] == head for line in git(target, "bundle", "list-heads", str(path)).splitlines()):
                if restore:
                    with tempfile.TemporaryDirectory(prefix="cleanup-bundle-check-") as directory:
                        recovered = Path(directory) / "restored.git"
                        git(Path(directory), "-c", "core.hooksPath=/dev/null", "clone", "--bare", "--no-local", "--no-hardlinks", str(path), str(recovered))
                        require(git(recovered, "cat-file", "-t", head).strip() == "commit" and git(recovered, "cat-file", "-t", head + "^{tree}").strip() == "tree", "Bundle does not restore the expected commit and tree")
                        git(recovered, "fsck", "--full", "--no-reflogs")
                bundles.append(name)
    require(all(name in manifest and (archive / name).stat().st_size for name in ("PRD.md", "BOARD.md")), "PRD or BOARD archive missing or empty")
    require(any(name.startswith("reviews/") and Path(name).suffix in (".md", ".json", ".jsonl", ".txt") and (archive / name).read_bytes().strip() for name in manifest), "No archived review record")
    require(bundles, "No self-contained Git bundle retains the expected HEAD")
    return archive, manifest


def check_activity(activity, task, target, now):
    require(isinstance(activity, dict) and activity.get("source") == "codex-app" and activity.get("complete") is True, "Fresh complete Codex app activity evidence is required")
    age = (now - utc(activity["captured_at"])).total_seconds()
    require(0 <= age <= 300, "Activity evidence is stale or in the future")
    threads, ids = activity["threads"], task["thread_ids"]
    require(isinstance(threads, list) and isinstance(ids, list) and ids and all(isinstance(i, str) and i for i in ids), "Invalid thread activity or registration")
    seen = {}
    for thread in threads:
        require(isinstance(thread, dict) and isinstance(thread["id"], str) and thread["id"] not in seen and
                isinstance(thread["worktree"], str) and isinstance(thread["status"], str), "Incomplete or duplicate activity rows")
        seen[thread["id"]] = thread
        if Path(thread["worktree"]).resolve() == target or thread["id"] in ids:
            require(thread["status"] not in ("running", "waiting", "planning"), "A task thread is active", "blocked")
            require(thread["status"] in ("idle", "completed", "archived"), "Unknown thread activity status")
    require(all(i in seen for i in ids), "Registered task threads are missing from activity evidence")
    require(all(Path(seen[i]["worktree"]).resolve() == target for i in ids), "Registered thread worktree identity differs")


def refresh_prs(api, mappings, head):
    actor = api("user")
    require(actor["login"] == AUTHOR, "Authenticated GitHub account differs")
    result = {"login": actor["login"]}
    for label, expected_repo, mapping in zip(("fork", "upstream"), (FORK, UPSTREAM), mappings):
        require(mapping["repo"] == expected_repo and type(mapping["number"]) is int and mapping["number"] > 0 and
                mapping["base"] == "main" and mapping["head_sha"] == head and
                isinstance(mapping["head_repo"], str) and mapping["head_repo"] and isinstance(mapping["head_branch"], str) and mapping["head_branch"], "Invalid exact PR identity mapping")
        pr = api(f"repos/{expected_repo}/pulls/{mapping['number']}")
        identity = {"repo": pr["base"]["repo"]["full_name"], "number": pr["number"], "head_repo": pr["head"]["repo"]["full_name"],
                    "head_branch": pr["head"]["ref"], "head_sha": pr["head"]["sha"], "base": pr["base"]["ref"]}
        require(identity == {key: mapping[key] for key in identity} and pr["user"]["login"] == AUTHOR, "Live PR identity or author differs from mapping")
        require(pr["state"] in ("open", "closed") and type(pr["merged"]) is bool, "Unknown PR state")
        result[label] = {**identity, "author": pr["user"]["login"], "state": pr["state"], "merged": pr["merged"], "merged_at": pr["merged_at"]}
    return result


def snapshot(repo):
    fields = {"head": ("rev-parse", "HEAD"), "branch": ("symbolic-ref", "-q", "HEAD"),
              "git_dir": ("rev-parse", "--absolute-git-dir"), "common_dir": ("rev-parse", "--git-common-dir"),
              "status": ("status", "--porcelain=v1", "-z", "--untracked-files=all", "--ignored=traditional"),
              "flags": ("ls-files", "-v", "-z"), "index": ("ls-files", "--stage", "-z")}
    state = {key: git(repo, *args) for key, args in fields.items()}
    state["operations"] = []
    for directory in (Path(state["git_dir"].strip()), (repo / state["common_dir"].strip()).resolve()):
        for name in ("MERGE_HEAD", "CHERRY_PICK_HEAD", "REVERT_HEAD", "BISECT_LOG", "rebase-merge", "rebase-apply", "sequencer", "index.lock", "HEAD.lock", "packed-refs.lock", "shallow.lock"):
            if (directory / name).exists():
                state["operations"].append(str(directory / name))
        if (directory / "refs").is_dir():
            state["operations"].extend(str(p) for p in sorted((directory / "refs").rglob("*.lock")))
    return state


def worktrees(repo):
    return [dict(field.split(" ", 1) if " " in field else (field, "") for field in block.split("\0") if field)
            for block in git(repo, "worktree", "list", "--porcelain", "-z").split("\0\0") if block.strip("\0")]


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), "-c", "core.fsmonitor=false", *args], capture_output=True, check=True,
                          text=True, timeout=30, env=dict(os.environ, GIT_OPTIONAL_LOCKS="0", GIT_NO_REPLACE_OBJECTS="1", LC_ALL="C")).stdout


def github(endpoint):
    return json.loads(subprocess.run(["gh", "api", "--method", "GET", endpoint], capture_output=True, check=True, text=True, timeout=30).stdout)


def utc(value):
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    require(result.tzinfo is not None and result.utcoffset().total_seconds() == 0, "Timestamp must be UTC")
    return result


def beneath(path, parent):
    return path == parent or parent in path.parents


def symlink_path(path):
    return any(p.is_symlink() for p in (path, *path.parents))


def sha(value):
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{40}(?:[0-9a-f]{24})?", value)


def require(condition, reason, status="unknown"):
    if not condition:
        raise GuardIssue(status, reason)


class GuardIssue(ValueError):
    def __init__(self, status, reason):
        super().__init__(reason)
        self.status = status


if __name__ == "__main__":
    sys.exit(main())
