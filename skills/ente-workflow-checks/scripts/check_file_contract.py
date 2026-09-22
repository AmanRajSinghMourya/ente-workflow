#!/usr/bin/env python3
"""Check a task's exact checkout, file scope and approved file expectations."""

import argparse
import fnmatch
import json
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode = True
import checks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--contract", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = verify(checks.repository(args.repo), json.loads(args.contract.read_text()))
        print(json.dumps(result, indent=2))
        return {"pass": 0, "fail": 1, "incomplete": 2}[result["status"]]
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        print(json.dumps({"status": "incomplete", "error": str(error)}, indent=2))
        return 2


def verify(repo, contract):
    validate(contract)
    results = []

    def require(name, condition, path=None):
        item = {"check": name, "status": "pass" if condition else "fail"}
        if path is not None:
            item["path"] = path
        results.append(item)

    require("selected_repository", str(repo) == contract["repo"])
    if results[-1]["status"] == "fail":
        return checks.report(results)
    before = checks.investigation_state(repo)
    if "branch" in contract:
        require("selected_branch", before["branch"] == contract["branch"])
    if "head" in contract:
        require("selected_revision", before["head"] == contract["head"])

    changed = set()
    if "allowed_paths" in contract:
        base = contract["base"]
        checks.git(repo, "cat-file", "-e", base + "^{commit}")
        # Check final worktree and index independently, including both sides of renames.
        for args in ((), ("--cached",)):
            output = checks.git(repo, "diff", "--no-ext-diff", "--no-textconv", "--ignore-submodules=none", "--no-renames", "--name-only", "-z", *args, base)
            changed.update(p for p in output.split("\0") if p)
        changed.update(p for p in checks.git(repo, "ls-files", "--others", "--exclude-standard", "-z").split("\0") if p)
        for name in sorted(changed):
            require("permitted_file", any(fnmatch.fnmatchcase(name, pattern) for pattern in contract["allowed_paths"]), name)
        for name in contract.get("must_change", []):
            require("required_changed_file", name in changed, name)

    staged = set()
    unstaged = set()
    if contract.get("files"):
        for target, args in ((staged, ("--cached", "HEAD")), (unstaged, ())):
            output = checks.git(repo, "diff", "--no-ext-diff", "--no-textconv", "--ignore-submodules=none", "--no-renames", "--name-only", "-z", *args)
            target.update(p for p in output.split("\0") if p)
    for expected in contract.get("files", []):
        name = expected["path"]
        path = repo / name
        require("staged_file_matches_worktree", name not in staged or name not in unstaged, name)
        # A link to a different document is not the declared artifact.
        require("exact_file_location", path.resolve() == path, name)
        if path.resolve() != path:
            continue
        if expected.get("absent"):
            require("intentional_absence", not path.exists(), name)
            continue
        require("required_file_exists", path.is_file(), name)
        if not path.is_file():
            continue
        if "sha256" in expected:
            require("preserved_file_bytes", checks.file_hash(path) == expected["sha256"], name)
        if "text" in expected:
            require("approved_file_text", path.read_bytes().decode("utf-8") == expected["text"], name)
        if "json_values" in expected:
            actual = json.loads(path.read_text())
            if not isinstance(actual, dict):
                raise ValueError("Expected a JSON object in " + name)
            for key, value in expected["json_values"].items():
                # Values stay out of reports; localization/copy may contain private context.
                require("approved_json_value:" + key, key in actual and json.dumps(actual[key], sort_keys=True) == json.dumps(value, sort_keys=True), name)
    require("checkout_unchanged_during_check", before == checks.investigation_state(repo))
    return checks.report(results, checked_at=checks.now(), changed_paths=sorted(changed))


def validate(contract):
    supported = {"repo", "branch", "head", "base", "allowed_paths", "must_change", "files"}
    if not isinstance(contract, dict) or set(contract) - supported:
        raise ValueError("Unknown contract fields; no assertions are silently ignored.")
    root = contract.get("repo")
    if not isinstance(root, str) or not Path(root).is_absolute() or str(Path(root).resolve()) != root:
        raise ValueError("repo must be the exact absolute real path selected for the task.")
    for key in ("head", "base"):
        if key in contract and (not isinstance(contract[key], str) or len(contract[key]) != 40 or any(c not in "0123456789abcdef" for c in contract[key])):
            raise ValueError(key + " must be a full, fixed commit SHA, not a moving branch name.")
    if "branch" in contract and not isinstance(contract["branch"], str):
        raise ValueError("branch must be a string (empty for detached HEAD).")
    for key in ("allowed_paths", "must_change"):
        if key in contract:
            if not isinstance(contract[key], list):
                raise ValueError(key + " must be a list.")
            for name in contract[key]:
                relative_path(name)
    if "allowed_paths" in contract and "base" not in contract:
        raise ValueError("allowed_paths needs a fixed base SHA.")
    if "must_change" in contract and "allowed_paths" not in contract:
        raise ValueError("must_change needs allowed_paths and base.")
    files = contract.get("files", [])
    if not isinstance(files, list):
        raise ValueError("files must be a list.")
    for item in files:
        if not isinstance(item, dict) or set(item) - {"path", "sha256", "text", "json_values", "absent"}:
            raise ValueError("Unknown file expectation.")
        relative_path(item.get("path"))
        assertions = set(item) - {"path"}
        if not assertions or ("absent" in item and (item["absent"] is not True or len(assertions) != 1)):
            raise ValueError("A file needs explicit content expectations or absent: true.")
        if "sha256" in item and (not isinstance(item["sha256"], str) or len(item["sha256"]) != 64 or any(c not in "0123456789abcdef" for c in item["sha256"])):
            raise ValueError("sha256 must contain 64 lowercase hexadecimal characters.")
        if "text" in item and not isinstance(item["text"], str):
            raise ValueError("text must be the exact approved string.")
        if "json_values" in item and (not isinstance(item["json_values"], dict) or not item["json_values"]):
            raise ValueError("json_values must contain the selected expected keys and values.")
    if "allowed_paths" not in contract and not files and "head" not in contract and "branch" not in contract:
        raise ValueError("The contract needs a scope, file, revision or branch assertion.")


def relative_path(name):
    if not isinstance(name, str) or not name or Path(name).is_absolute() or any(p in ("", ".", "..", ".git") for p in name.split("/")):
        raise ValueError("Expected a repository-relative file path or scope glob: " + repr(name))


if __name__ == "__main__":
    sys.exit(main())
