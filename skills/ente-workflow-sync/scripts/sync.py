#!/usr/bin/env python3
"""Sync the private workflow repository and its owned personal skill links."""

import argparse
from datetime import datetime, timezone
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile


DEFAULT_ROOT = Path(__file__).resolve().parents[3]
MAX_FILE_BYTES = 10 * 1024 * 1024
SECRET = re.compile(
    rb"gh[op]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|"
    rb"sk-[A-Za-z0-9_-]{20,}|-----BEGIN (?:[A-Z0-9 ]* )?PRIVATE KEY-----"
)


class SyncError(Exception):
    def __init__(self, message, status="pending"):
        super().__init__(message)
        self.status = status


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("command", choices=("sync", "links"))
    args = parser.parse_args()
    if not args.root.is_absolute():
        print(json.dumps({"status": "pending", "error": "--root must be absolute"}))
        return 1
    root = args.root.resolve()
    result = {"status": "pending", "time": now()}
    try:
        state = root / ".workflow"
        state.mkdir(exist_ok=True)
        with (state / "sync.lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            try:
                config = read_config(root)
                if args.command == "sync":
                    sync(root, config)
                else:
                    reconcile_links(root, config)
                result = {"status": "ok", "time": now()}
                previous = state / "sync-status.json"
                if args.command == "links" and previous.is_file():
                    prior = json.loads(previous.read_text())
                    if prior.get("status") in {"pending", "conflict"}:
                        result = prior
            except SyncError as error:
                result = {"status": error.status, "time": now(), "error": str(error)}
            except (OSError, ValueError):
                result = {"status": "pending", "time": now(),
                          "error": "Local workflow files could not be read or updated"}
            write_status(root, result)
            # Refresh the reader after writing this run's result, including failures.
            try:
                render_todo(root)
            except (SyncError, OSError, ValueError):
                pass
    except OSError:
        result = {"status": "pending", "time": now(),
                  "error": "Workflow sync lock or status file is unavailable"}
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["status"] == "ok" else 1


def sync(root, config):
    validate_repository(root, config)
    check_operation_state(root)
    if git(root, "diff", "--cached", "--quiet", allowed=(0, 1)).returncode:
        raise SyncError("Staged changes belong to the user; sync did not touch them")
    check_candidates(root)
    # Recheck after inspection so an intervening user staging operation is not committed.
    if git(root, "diff", "--cached", "--quiet", allowed=(0, 1)).returncode:
        raise SyncError("The index changed during inspection; sync stopped")
    require_main(root)
    git(root, "add", "-A", "--", ".")
    check_index(root)
    if git(root, "diff", "--cached", "--quiet", allowed=(0, 1)).returncode:
        require_main(root)
        git(root, "commit", "-m", "Sync workflow on " + config["machine"])
    require_clean(root)
    git(root, "fetch", "origin", "main", error="Fetch failed; local work is saved for a later retry")
    require_clean(root)
    require_main(root)
    merged = git(root, "merge", "--no-edit", "origin/main", allowed=(0, 1, 128))
    if merged.returncode:
        if git(root, "ls-files", "--unmerged", "-z").stdout:
            raise SyncError("Conflicting edits need review; both commits are preserved", "conflict")
        raise SyncError("Merge stopped; local and remote commits are preserved")
    check_candidates(root)
    reconcile_links(root, config)
    render_todo(root)
    require_clean(root)
    require_main(root)
    git(root, "push", "origin", "HEAD:main",
        error="Push failed; local work is saved for a later retry")


def read_config(root):
    try:
        config = json.loads((root / ".workflow/local.json").read_text())
    except (OSError, ValueError):
        raise SyncError("A valid .workflow/local.json is required")
    if not isinstance(config, dict) or config.get("machine") not in {"macbook-air", "mac-mini"}:
        raise SyncError("Local config must identify macbook-air or mac-mini")
    remote = config.get("expected_remote")
    if not isinstance(remote, str) or not remote or "\n" in remote:
        raise SyncError("Local config must specify expected_remote")
    paths = config.get("skill_roots")
    if not isinstance(paths, list) or not paths:
        raise SyncError("Local config must specify personal skill_roots")
    if any(not isinstance(path, str) or not Path(path).is_absolute() for path in paths):
        raise SyncError("Every personal skills path must be absolute")
    if any(inside(Path(path).resolve(), root) for path in paths):
        raise SyncError("Personal skill links must live outside the shared repository")
    return config


def validate_repository(root, config):
    top = git(root, "rev-parse", "--show-toplevel", error="Workflow root is not a Git repository")
    if Path(top.stdout.decode().strip()).resolve() != root:
        raise SyncError("Workflow root must be the exact Git repository root")
    for flags in (("--all",), ("--push", "--all")):
        remote = git(root, "remote", "get-url", *flags, "origin",
                     error="The origin remote is missing").stdout.decode().splitlines()
        if remote != [config["expected_remote"]]:
            raise SyncError("Origin fetch and push URLs must match the configured remote exactly")


def check_operation_state(root):
    if git(root, "ls-files", "--unmerged", "-z").stdout:
        raise SyncError("An unresolved Git conflict needs review", "conflict")
    for name in ("MERGE_HEAD", "rebase-merge", "rebase-apply"):
        output = git(root, "rev-parse", "--git-path", name).stdout.decode().strip()
        path = Path(output)
        if not path.is_absolute():
            path = root / path
        if path.exists():
            raise SyncError("An existing merge or rebase must be completed first", "conflict")


def check_candidates(root):
    skills = root / "skills"
    if skills.exists():
        for directory, subdirs, files in os.walk(skills, followlinks=False):
            if ".git" in subdirs or ".git" in files:
                relative = (Path(directory) / ".git").relative_to(root)
                raise SyncError(display_path(relative) + ": nested Git repository must be excluded")
    output = git(root, "ls-files", "--cached", "--others", "--exclude-standard", "-z").stdout
    for name in set(output.split(b"\0")) - {b""}:
        relative = Path(os.fsdecode(name))
        path = root / relative
        check_name(relative)
        if path.is_symlink() and not inside(path.resolve(), root):
            raise SyncError(display_path(relative) + ": symlink points outside the workflow repository")
        if not path.exists():
            continue
        if path.is_dir():
            if not path.is_symlink():
                raise SyncError(display_path(relative) + ": nested repository or directory in Git file list")
            continue
        if path.stat().st_size > MAX_FILE_BYTES:
            raise SyncError(display_path(relative) + ": exceeds the 10 MiB limit")
        check_blob(relative, path.read_bytes())


def check_index(root):
    entries, objects = [], {}
    for entry in git(root, "ls-files", "--stage", "-z").stdout.split(b"\0"):
        if not entry:
            continue
        metadata, name = entry.split(b"\t", 1)
        mode, oid, stage = metadata.split()
        relative = Path(os.fsdecode(name))
        check_name(relative)
        if stage != b"0":
            raise SyncError(display_path(relative) + ": unresolved index conflict", "conflict")
        if mode not in {b"100644", b"100755", b"120000"}:
            raise SyncError(display_path(relative) + ": unsupported Git entry or nested repository")
        entries.append((relative, mode, oid))
        objects.setdefault(oid, relative)
    if not entries:
        return
    request = b"\n".join(objects) + b"\n"
    sizes = git(root, "cat-file", "--batch-check", input_bytes=request).stdout.splitlines()
    for (oid, relative), header in zip(objects.items(), sizes):
        fields = header.split()
        if len(fields) != 3 or fields[:2] != [oid, b"blob"]:
            raise SyncError(display_path(relative) + ": staged object is not an available blob")
        if int(fields[2]) > MAX_FILE_BYTES:
            raise SyncError(display_path(relative) + ": staged file exceeds the 10 MiB limit")
    output = git(root, "cat-file", "--batch", input_bytes=request).stdout
    blobs, offset = {}, 0
    for oid, relative in objects.items():
        end = output.index(b"\n", offset)
        size = int(output[offset:end].split()[2])
        blob = output[end + 1:end + 1 + size]
        check_blob(relative, blob)
        blobs[oid] = blob
        offset = end + size + 2
    for relative, mode, oid in entries:
        if mode == b"120000":
            target = blobs[oid]
            try:
                resolved = (root / relative.parent / os.fsdecode(target)).resolve()
            except (OSError, ValueError, RuntimeError):
                raise SyncError(display_path(relative) + ": staged symlink target is invalid")
            if not inside(resolved, root):
                raise SyncError(display_path(relative) + ": staged symlink points outside the workflow repository")


def check_name(relative):
    if relative.is_absolute() or ".." in relative.parts:
        raise SyncError("Git contains a path outside the workflow repository")
    if any(credential_name(part) for part in relative.parts):
        raise SyncError(display_path(relative) + ": credential-named file is excluded from sync")


def check_blob(relative, blob):
    if SECRET.search(blob):
        raise SyncError(display_path(relative) + ": credential pattern found; contents were not uploaded")


def display_path(relative):
    safe = SECRET.sub(b"[credential]", os.fsencode(relative)).decode("utf-8", "replace")
    return json.dumps(safe, ensure_ascii=True)


def reconcile_links(root, config):
    source = root / "skills"
    if source.exists() and not inside(source.resolve(), root):
        raise SyncError("Shared skills must live inside the workflow repository")
    desired = {}
    if source.exists():
        desired = {folder.name: folder for folder in source.iterdir()
                   if folder.is_dir() and ((folder / "SKILL.md").is_file() or folder.name == "_licenses")}
    for folder in desired.values():
        if not inside(folder.resolve(), root):
            raise SyncError("A shared skill points outside the workflow repository")
    additions, removals = [], []
    destinations = {Path(path).resolve() for path in config["skill_roots"]}
    for destination in destinations:
        if destination.exists() and not destination.is_dir():
            raise SyncError("A personal skills path is not a directory")
        for name, folder in desired.items():
            link = destination / name
            if link.is_symlink() and lexical_target(link) == folder:
                continue
            if link.exists() or link.is_symlink():
                raise SyncError("A personal skill name is already owned by another file or link")
            additions.append((link, folder))
        if destination.is_dir():
            for link in destination.iterdir():
                if not link.is_symlink():
                    continue
                target = lexical_target(link)
                if target.parent == source and target.name not in desired:
                    removals.append(link)
    for destination in destinations:
        destination.mkdir(parents=True, exist_ok=True)
    for link, folder in additions:
        link.symlink_to(folder, target_is_directory=True)
    for link in removals:
        link.unlink()


def render_todo(root):
    path = root / "skills/ente-task-queue/scripts/queue.py"
    if path.is_file():
        spec = importlib.util.spec_from_file_location("workflow_queue", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        if not callable(getattr(module, "render_view", None)):
            raise SyncError("Queue helper needs its lock-free render_view function before syncing")
        try:
            module.render_view(root)
        except (OSError, ValueError):
            raise SyncError("Task view regeneration failed; shared work is preserved")


def require_clean(root):
    if git(root, "status", "--porcelain", "-z").stdout:
        raise SyncError("Files changed during sync; work is preserved for the next run")


def require_main(root):
    branch = git(root, "symbolic-ref", "--quiet", "HEAD", allowed=(0, 1)).stdout.strip()
    if branch != b"refs/heads/main":
        raise SyncError("Automatic sync requires branch main; detached HEAD and other branches are left untouched")


def git(root, *arguments, allowed=(0,), error=None, input_bytes=None):
    environment = {**os.environ, "GIT_TERMINAL_PROMPT": "0", "GCM_INTERACTIVE": "Never",
                   "GIT_EDITOR": "true", "GIT_MERGE_AUTOEDIT": "no",
                   "GIT_SSH_COMMAND": "ssh -o BatchMode=yes -o ConnectTimeout=15"}
    try:
        result = subprocess.run(["git", "-C", str(root), *arguments], capture_output=True,
                                env=environment, timeout=90, input=input_bytes)
    except subprocess.TimeoutExpired:
        raise SyncError("Git operation timed out; retry after checking the repository")
    if result.returncode not in allowed:
        raise SyncError(error or "Git " + arguments[0] + " failed; repository state is preserved")
    return result


def credential_name(name):
    lowered = name.lower()
    return (lowered == ".env" or lowered.startswith(".env.") or
            lowered.endswith((".pem", ".key")) or lowered in {"auth.json", "credentials.json"})


def inside(path, root):
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def lexical_target(link):
    return Path(os.path.abspath(os.path.join(str(link.parent), os.readlink(link))))


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def write_status(root, value):
    directory = root / ".workflow"
    with tempfile.NamedTemporaryFile(mode="w", dir=directory, prefix=".sync-", delete=False) as stream:
        path = Path(stream.name)
        json.dump(value, stream, ensure_ascii=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    try:
        os.replace(path, directory / "sync-status.json")
    finally:
        path.unlink(missing_ok=True)


if __name__ == "__main__":
    sys.exit(main())
