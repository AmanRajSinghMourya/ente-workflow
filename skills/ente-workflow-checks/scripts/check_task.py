#!/usr/bin/env python3
"""Check a PRD's byte ceiling or the actual size of a task. Python 3.9+, stdlib."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

sys.dont_write_bytecode = True
import checks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    prd = sub.add_parser("prd", help="Check a UTF-8 PRD, optionally against an earlier digest")
    prd.add_argument("--prd", type=Path, required=True)
    prd.add_argument("--sha256")
    diff = sub.add_parser("diff", help="Count explicit ancestor base to final working tree")
    diff.add_argument("--repo", type=Path, required=True)
    diff.add_argument("--base", required=True)
    args = parser.parse_args()
    try:
        result = check_prd(args.prd, args.sha256) if args.action == "prd" else measure_diff(args.repo, args.base)
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        result = {"status": "incomplete", "error": str(error)}
    print(json.dumps(result, indent=2))
    return {"pass": 0, "fail": 1, "incomplete": 2}[result["status"]]


def check_prd(path, expected_sha256=None):
    data = path.read_bytes()
    result = {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
    try:
        content = data.decode("utf-8")
    except UnicodeDecodeError as error:
        return {**result, "status": "incomplete", "error": str(error)}
    errors = []
    if not content.strip():
        errors.append("PRD is empty.")
    if len(data) > 50000:
        errors.append("PRD exceeds 50,000 UTF-8 bytes.")
    if expected_sha256 is not None and expected_sha256 != result["sha256"]:
        errors.append("PRD differs from the expected SHA-256 digest.")
    return {**result, "status": "fail" if errors else "pass", "errors": errors}


def measure_diff(path, base):
    repo = checks.repository(path)
    if not re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", base):
        raise ValueError("--base must be a full commit SHA, not a moving branch or abbreviated SHA.")
    if checks.git(repo, "cat-file", "-t", base).strip() != "commit":
        raise ValueError("--base must identify a commit.")
    before = checks.fingerprint(repo)
    staged = set(checks.git(repo, "diff", "--cached", "--name-only", "-z", "HEAD", "--").split("\0"))
    unstaged = set(checks.git(repo, "diff", "--name-only", "-z", "--").split("\0"))
    divergent = sorted((staged & unstaged) - {""})
    if divergent:
        raise ValueError("Staged and working-tree versions differ; resolve the intended version before counting: " + repr(divergent))
    if checks.git(repo, "merge-base", base, before["head"]).strip() != base:
        raise ValueError("--base must be an ancestor of HEAD.")
    options = ["--no-ext-diff", "--no-textconv", "--no-renames", "--no-color", "--diff-algorithm=myers", "--no-indent-heuristic", "--numstat", "-z"]
    command = ["git", "-C", str(repo), "diff", *options]
    files = parse_numstat(checks.execute([*command, "--ignore-submodules=none", base, "--"]))
    tracked_paths = {entry["path"] for entry in files}
    for name in checks.git(repo, "ls-files", "--others", "--exclude-standard", "-z").split("\0"):
        if not name:
            continue
        if name in tracked_paths:
            raise ValueError("An index deletion has an untracked replacement; resolve staging before counting: " + name)
        process = subprocess.run([*command, "--no-index", "--", os.devnull, str(repo / name)], capture_output=True, env=dict(os.environ, GIT_OPTIONAL_LOCKS="0", GIT_NO_REPLACE_OBJECTS="1"))
        if process.returncode not in (0, 1):
            raise ValueError(process.stderr.decode(errors="replace").strip())
        entries = parse_numstat(process.stdout)
        if len(entries) != 1:
            raise ValueError("Cannot measure untracked path: " + name)
        files.append({**entries[0], "path": name})
    if before != checks.fingerprint(repo):
        raise ValueError("Repository changed while its diff was being measured; run the check again.")
    additions = sum(entry["additions"] or 0 for entry in files)
    deletions = sum(entry["deletions"] or 0 for entry in files)
    total = additions + deletions
    binaries = [entry["path"] for entry in files if entry["binary"]]
    return {
        "status": "fail" if total > 1000 else "incomplete" if binaries else "pass",
        "repo": str(repo), "base": base,
        "added_lines": additions, "deleted_lines": deletions, "changed_lines": total,
        "line_count_complete": not binaries, "files": files, "binaries": binaries,
        "warnings": ["Above the 500-line target; consider a smaller task."] if total > 500 else [],
        "errors": ["Above the 1,000-line limit; split or re-plan before proceeding."] if total > 1000 else [],
    }


def parse_numstat(data):
    records = iter(data.split(b"\0"))
    files = []
    for record in records:
        if not record:
            continue
        added, deleted, path = record.split(b"\t", 2)
        if not path:
            # --no-index emits both paths even with --no-renames.
            next(records)
            path = next(records)
        binary = added == deleted == b"-"
        files.append({"path": os.fsdecode(path), "additions": None if binary else int(added), "deletions": None if binary else int(deleted), "binary": binary})
    return files


if __name__ == "__main__":
    sys.exit(main())
