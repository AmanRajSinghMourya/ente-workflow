#!/usr/bin/env python3
"""Read-only PR preflight and validation freshness checks. Python 3.9+, no packages."""

import argparse
from datetime import datetime, timezone
import fnmatch
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from urllib.parse import quote, urlsplit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    pr = sub.add_parser("pr", help="Check a pushed branch before opening/updating its PR")
    pr.add_argument("--repo", required=True, type=Path)
    pr.add_argument("--contract", required=True, type=Path)
    pr.add_argument("--offline", action="store_true", help="Local checks only; cannot return a full pass")
    run = sub.add_parser("run", help="Run an approved validation command and record its code version")
    run.add_argument("--repo", required=True, type=Path)
    run.add_argument("--cwd", default=".", help="Command directory relative to repository root")
    run.add_argument("--receipt", required=True, type=Path)
    run.add_argument("command", nargs=argparse.REMAINDER)
    verify = sub.add_parser("verify", help="Reject failed/stale checks or altered check logs")
    verify.add_argument("--repo", required=True, type=Path)
    verify.add_argument("--receipt", required=True, type=Path)
    for action in ("snapshot", "unchanged"):
        check = sub.add_parser(action, help="Record/check repository state for an investigation")
        check.add_argument("--repo", required=True, type=Path)
        check.add_argument("--snapshot", required=True, type=Path)
    args = parser.parse_args()
    try:
        repo = repository(args.repo)
        if args.action == "pr":
            result = preflight(repo, read_contract(args.contract), offline=args.offline)
        elif args.action == "run":
            command = args.command[1:] if args.command[:1] == ["--"] else args.command
            result = run_validation(repo, args.cwd, args.receipt, command)
        elif args.action == "verify":
            result = verify_validation(repo, args.receipt)
        elif args.action == "snapshot":
            result = save_snapshot(repo, args.snapshot)
        else:
            previous = json.loads(args.snapshot.read_text())
            actual = investigation_state(repo)
            result = report([{"check": "investigation_left_repository_unchanged", "status": "pass" if previous["repo"] == str(repo) and previous["state"] == actual else "fail", "detail": "Detection only; differences may also be caused by another task or user."}], previous=previous["state"], actual=actual)
        print(json.dumps(result, indent=2))
        return {"pass": 0, "fail": 1, "incomplete": 2}[result["status"]]
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        print(json.dumps({"status": "incomplete", "error": str(error)}, indent=2))
        return 2


def preflight(repo, contract, offline=False, api=None):
    """The API injectable argument exists only for replay tests, never CLI input."""
    checks = []
    starting_state = investigation_state(repo)

    def check(name, condition, detail):
        checks.append({"check": name, "status": "pass" if condition else "fail", "detail": detail})

    head = git(repo, "rev-parse", "HEAD").strip()
    branch = git(repo, "branch", "--show-current").strip()
    check("task_branch", branch == contract["branch"], {"expected": contract["branch"], "actual": branch})
    dirty = git(repo, "status", "--porcelain=v1", "--untracked-files=all")
    check("published_code_is_working_code", not dirty, "Clean" if not dirty else dirty.splitlines())
    urls = git(repo, "remote", "get-url", "--push", "--all", contract["remote"]).splitlines()
    check("push_destination", urls == [contract["push_url"]], {"expected": contract["push_url"], "actual": urls})
    url = contract["push_url"]
    path = urlsplit(url).path if "://" in url else url.split(":", 1)[-1]
    push_repo = path.strip("/").removesuffix(".git")
    for key in ("name", "email"):
        value = git(repo, "config", "--local", "--get", "user." + key, optional=True).strip()
        check("local_author_" + key, value == contract["author"][key], {"expected": contract["author"][key], "actual": value})

    if offline:
        checks.append({"check": "github_state", "status": "incomplete", "detail": "Remote base, pushed head, API account and PR identity were not queried."})
        return report(checks, head=head, checked_at=now())

    api = api or github
    canonical_names = {}

    def canonical_repo(name):
        key = name.casefold()
        if key not in canonical_names:
            canonical_names[key] = api("repos/" + name)["full_name"].casefold()
        return canonical_names[key]

    check("push_url_matches_head_repository", canonical_repo(push_repo) == canonical_repo(contract["head_repo"]), {"push_repo": push_repo, "head_repo": contract["head_repo"]})
    login = api("user")["login"]
    check("github_api_account", login.casefold() == contract["api_login"].casefold(), {"expected": contract["api_login"], "actual": login})

    def remote_sha(name, ref):
        result = api("repos/" + name + "/git/ref/heads/" + quote(ref, safe=""))
        if result["ref"] != "refs/heads/" + ref or result["object"]["type"] != "commit":
            raise ValueError("Expected an exact branch reference: " + name + ":" + ref)
        return result["object"]["sha"]

    base = remote_sha(contract["target_repo"], contract["base_branch"])
    pushed = remote_sha(contract["head_repo"], contract["branch"])
    check("pushed_head", pushed == head, {"local": head, "remote": pushed})
    if contract.get("match_upstream"):
        upstream = remote_sha(contract["upstream_repo"], contract["base_branch"])
        check("fork_base_matches_upstream", base == upstream, {"fork": base, "upstream": upstream})

    # Use the actual remote base SHA, not a possibly stale local origin/main.
    git(repo, "cat-file", "-e", base + "^{commit}")
    changed = git(repo, "diff", "--no-ext-diff", "--no-textconv", "--ignore-submodules=none", "--no-renames", "--name-only", "-z", base + "..." + head).split("\0")
    changed = [path for path in changed if path]
    extra = [path for path in changed if not any(fnmatch.fnmatchcase(path, pattern) for pattern in contract["allowed_paths"])]
    check("change_scope", not extra, {"changed_paths": changed, "unexpected_paths": extra})
    check("nonempty_change", bool(changed), "The candidate must contain a change relative to its actual PR base.")
    commits = git(repo, "rev-list", base + ".." + head).splitlines()
    if "expected_commits" in contract:
        check("candidate_commits", set(commits) == set(contract["expected_commits"]), {"expected": contract["expected_commits"], "actual": commits})
    if contract.get("pr_number"):
        pr = api("repos/" + contract["target_repo"] + "/pulls/" + str(contract["pr_number"]))
        actual = {"target_repo": pr["base"]["repo"]["full_name"], "head_repo": pr["head"]["repo"]["full_name"], "base_branch": pr["base"]["ref"], "branch": pr["head"]["ref"], "head": pr["head"]["sha"]}
        expected = {key: contract[key] for key in ("target_repo", "head_repo", "base_branch", "branch")}
        expected["head"] = head
        for key in ("target_repo", "head_repo"):
            expected[key] = canonical_repo(expected[key])
            actual[key] = actual[key].casefold()
        check("existing_pr_identity", actual == expected, {"expected": expected, "actual": actual})
    check("checkout_unchanged_during_preflight", starting_state == investigation_state(repo), "Refresh the check if another task or user changes the checkout.")
    return report(checks, head=head, base=base, commits=commits, commit_list_checked="expected_commits" in contract, checked_at=now())


def save_snapshot(repo, path):
    path = path.resolve()
    if path.is_relative_to(repo):
        raise ValueError("Store the snapshot outside the checked repository.")
    result = {"status": "pass", "repo": str(repo), "state": investigation_state(repo), "created_at": now()}
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as output:
        json.dump(result, output, indent=2)
        output.write("\n")
    return result


def investigation_state(repo):
    state = fingerprint(repo)
    state["branch"] = git(repo, "branch", "--show-current").strip()
    return state


def run_validation(repo, cwd, receipt_path, command):
    if not command:
        raise ValueError("Supply the validation command after --")
    receipt_path = receipt_path.resolve()
    if receipt_path.is_relative_to(repo):
        raise ValueError("Store the receipt outside the checked repository so it cannot change its own fingerprint.")
    workdir = (repo / cwd).resolve()
    if not workdir.is_relative_to(repo) or not workdir.is_dir():
        raise ValueError("Validation cwd must be a directory inside the repository.")
    log_path = receipt_path.with_suffix(receipt_path.suffix + ".log")
    if receipt_path.exists() or log_path.exists():
        raise ValueError("Use a new receipt path; existing evidence is never overwritten.")
    before = fingerprint(repo)
    started = now()
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("xb") as log:
        process = subprocess.run(command, cwd=workdir, stdout=log, stderr=subprocess.STDOUT)
    after = fingerprint(repo)
    result = {
        "status": "pass" if process.returncode == 0 and before == after else "fail",
        "repo": str(repo), "cwd": str(workdir), "command": command,
        "started_at": started, "finished_at": now(), "exit_code": process.returncode,
        "before": before, "after": after, "log": str(log_path),
        "log_sha256": file_hash(log_path),
        "limit": "Records command success and source freshness. Does not judge test coverage or prove device behavior.",
    }
    with receipt_path.open("x") as output:
        json.dump(result, output, indent=2)
        output.write("\n")
    return result


def verify_validation(repo, receipt_path):
    receipt = json.loads(receipt_path.read_text())
    current = fingerprint(repo)
    checks = [
        {"check": "same_repository", "status": "pass" if receipt["repo"] == str(repo) else "fail"},
        {"check": "command_passed", "status": "pass" if receipt["exit_code"] == 0 and receipt["status"] == "pass" else "fail"},
        {"check": "source_unchanged_during_check", "status": "pass" if receipt["before"] == receipt["after"] else "fail"},
        {"check": "source_still_matches", "status": "pass" if receipt["after"] == current else "fail"},
        {"check": "log_unchanged", "status": "pass" if file_hash(Path(receipt["log"])) == receipt["log_sha256"] else "fail"},
    ]
    return report(checks, command=receipt["command"], current=current)


def fingerprint(repo):
    """HEAD plus tracked/staged/worktree differences and nonignored untracked bytes."""
    head = git(repo, "rev-parse", "HEAD").strip()
    for item in git(repo, "ls-files", "-v", "-z").split("\0"):
        if item and (item[0].islower() or item[0] == "S"):
            raise ValueError("Git can hide changes to this path (assume-unchanged/skip-worktree): " + item[2:])
    # A dirty submodule's diff may say only '-dirty', hiding later content edits.
    for item in git(repo, "ls-files", "--stage", "-z").split("\0"):
        if item.startswith("160000 "):
            submodule = repo / item.split("\t", 1)[1]
            if submodule.is_dir() and (submodule / ".git").exists():
                if git(submodule, "status", "--porcelain=v1", "--untracked-files=all"):
                    raise ValueError("Cannot fingerprint a dirty submodule: " + str(submodule))
    digest = hashlib.sha256()
    diff = ["git", "-C", str(repo), "diff", "--no-ext-diff", "--no-textconv", "--ignore-submodules=none", "--binary"]
    digest.update(execute([*diff, "HEAD"]))
    index_digest = hashlib.sha256(execute([*diff, "--cached", "HEAD"])).hexdigest()
    files = git(repo, "ls-files", "--others", "--exclude-standard", "-z").split("\0")
    for name in sorted(path for path in files if path):
        path = repo / name
        digest.update(name.encode() + b"\0")
        if path.is_symlink():
            digest.update(b"link\0" + os.fsencode(os.readlink(path)))
        elif path.is_file():
            digest.update(b"file\0" + file_hash(path).encode())
            digest.update(str(path.stat().st_mode & 0o111).encode())
        else:
            raise ValueError("Untracked path is not a file: " + name)
        digest.update(b"\0")
    return {"head": head, "changes_sha256": digest.hexdigest(), "index_sha256": index_digest}


def read_contract(path):
    contract = json.loads(path.read_text())
    required = ("branch", "target_repo", "head_repo", "base_branch", "remote", "push_url", "api_login")
    for key in required:
        if not isinstance(contract.get(key), str) or not contract[key].strip():
            raise ValueError("Contract needs a nonempty " + key)
    for key in ("name", "email"):
        if not isinstance(contract.get("author", {}).get(key), str) or not contract["author"][key].strip():
            raise ValueError("Contract needs author." + key)
    paths = contract.get("allowed_paths")
    if not isinstance(paths, list) or not paths or any(not isinstance(p, str) or not p or p.startswith("/") or ".." in p.split("/") for p in paths):
        raise ValueError("allowed_paths must be a nonempty list of repository-relative paths/globs")
    if contract.get("match_upstream") and not contract.get("upstream_repo"):
        raise ValueError("match_upstream needs upstream_repo")
    if "match_upstream" in contract and not isinstance(contract["match_upstream"], bool):
        raise ValueError("match_upstream must be a JSON boolean")
    if "expected_commits" in contract:
        commits = contract["expected_commits"]
        if not isinstance(commits, list) or not commits or any(not isinstance(sha, str) or len(sha) != 40 or any(c not in "0123456789abcdef" for c in sha) for sha in commits):
            raise ValueError("expected_commits must be a nonempty list of full commit SHAs")
        if len(set(commits)) != len(commits):
            raise ValueError("expected_commits cannot contain duplicates")
    return contract


def repository(path):
    root = Path(git(path, "rev-parse", "--show-toplevel").strip()).resolve()
    if root != path.resolve():
        raise ValueError("--repo must identify the repository root, not a subdirectory")
    return root


def report(checks, **facts):
    statuses = {check["status"] for check in checks}
    status = "fail" if "fail" in statuses else "incomplete" if "incomplete" in statuses else "pass"
    return {"status": status, "checks": checks, **facts}


def github(endpoint):
    # GET only. Authentication is handled by gh; tokens are never read or logged.
    return json.loads(execute(["gh", "api", "--hostname", "github.com", "--method", "GET", endpoint]))


def git(repo, *args, optional=False):
    return execute(["git", "-C", str(repo), *args], optional=optional).decode()


def execute(command, optional=False):
    env = dict(os.environ, GIT_OPTIONAL_LOCKS="0", GIT_NO_REPLACE_OBJECTS="1")
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
    if result.returncode and not (optional and result.returncode == 1):
        raise ValueError(result.stderr.decode().strip() or "Command failed: " + " ".join(command))
    return result.stdout


def file_hash(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


if __name__ == "__main__":
    sys.exit(main())
