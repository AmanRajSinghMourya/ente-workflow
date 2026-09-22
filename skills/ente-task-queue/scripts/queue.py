#!/usr/bin/env python3
"""A locked Markdown task queue; entries are data, never executed."""

import argparse
import fcntl
import html
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from uuid import UUID


DEFAULT_FILE = "/Users/aman/Development/ente-workflow/TODO.md"
START, END = "<!-- queue:start -->", "<!-- queue:end -->"
COLUMNS = ("ID", "Task", "Status", "Codex task", "Context")
KEYS = ("id", "task", "status", "codex_task", "context")
STATES = ("queued", "starting", "planning", "needs decision", "implementing",
          "ready for review", "done", "deferred", "blocked")
LINK_REQUIRED = {"planning", "needs decision", "implementing", "ready for review", "done"}


class QueueError(ValueError):
    pass


def main():
    args = arguments()
    try:
        result = transact(args)
    except (QueueError, OSError, UnicodeError) as error:
        print(f"queue: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


def arguments():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", default=DEFAULT_FILE)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("list")
    add = commands.add_parser("add")
    add.add_argument("--title", required=True)
    add.add_argument("--context", required=True)
    destination = add.add_mutually_exclusive_group()
    destination.add_argument("--hold", action="store_true")
    destination.add_argument("--thread")
    commands.add_parser("claim")
    attach = commands.add_parser("attach")
    attach.add_argument("id")
    attach.add_argument("--thread", required=True)
    state = commands.add_parser("state")
    state.add_argument("id")
    state.add_argument("--from", dest="expected", choices=STATES, required=True)
    state.add_argument("--to", dest="target", choices=STATES, required=True)
    return parser.parse_args()


def transact(args):
    path = Path(args.file)
    if not path.is_absolute():
        raise QueueError("--file must be an absolute path")
    path = path.resolve()
    with path.with_name(".TODO.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        original = path.read_bytes().decode("utf-8")
        prefix, rows, suffix = parse(original)
        result, changed = change(rows, args)
        if changed:
            atomic_write(path, prefix + render(rows) + suffix)
        return result


def change(rows, args):
    if args.command == "list":
        return rows, False
    if args.command == "add":
        title = normalized(args.title)
        if not title:
            raise QueueError("task title must not be empty")
        url = thread_url(args.thread) if args.thread is not None else ""
        if url:
            existing = next((row for row in rows if row["codex_task"] == url), None)
            if existing:
                return existing, False
        duplicate = next((row for row in rows if normalized(row["task"]) == title), None)
        if duplicate:
            raise QueueError(f"title already exists as {duplicate['id']}; new context was not saved")
        number = max((int(row["id"][1:]) for row in rows), default=0) + 1
        status = "planning" if url else "deferred" if args.hold else "queued"
        row = dict(zip(KEYS, (f"Q{number:03}", args.title, status, url, args.context)))
        rows.append(row)
        return row, True
    if args.command == "claim":
        row = next((row for row in rows if row["status"] == "queued"), None)
        if row is None:
            return None, False
        row["status"] = "starting"
        return row, True
    row = next((row for row in rows if row["id"] == args.id), None)
    if row is None:
        raise QueueError(f"unknown task {args.id}")
    if args.command == "attach":
        url = thread_url(args.thread)
        if row["codex_task"] == url:
            return row, False
        if row["codex_task"]:
            raise QueueError(f"{args.id} already has a different Codex task")
        if row["status"] != "starting":
            raise QueueError(f"{args.id} must be starting before attachment")
        row["codex_task"], row["status"] = url, "planning"
        return row, True
    if row["status"] != args.expected:
        raise QueueError(f"{args.id} is {row['status']!r}, expected {args.expected!r}")
    if row["status"] == "starting" and args.target == "queued":
        raise QueueError("reconcile the existing dispatch first; starting cannot return directly to queued")
    if args.target in {"starting", "planning"}:
        raise QueueError("use claim or attach to enter starting or planning")
    if args.target in LINK_REQUIRED and not row["codex_task"]:
        raise QueueError(f"{args.target!r} requires a linked Codex task")
    if args.target == "queued" and row["codex_task"]:
        raise QueueError("a linked task cannot return to queued")
    changed = row["status"] != args.target
    row["status"] = args.target
    return row, changed


def parse(text):
    if text.count(START) != 1 or text.count(END) != 1:
        raise QueueError("expected exactly one queue:start and one queue:end marker")
    begin, end = text.index(START) + len(START), text.index(END)
    if begin > end:
        raise QueueError("queue:end must follow queue:start")
    lines = text[begin:end].strip().split("\n")
    if len(lines) < 2 or tuple(cells(lines[0])) != COLUMNS:
        raise QueueError("queue table must have columns: " + " | ".join(COLUMNS))
    if not all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells(lines[1])):
        raise QueueError("invalid queue table separator")
    rows, seen = [], set()
    for line in lines[2:]:
        row = dict(zip(KEYS, (html.unescape(cell) for cell in cells(line))))
        identifier = row["id"]
        if not re.fullmatch(r"Q[0-9]{3,}", identifier) or int(identifier[1:]) < 1:
            raise QueueError(f"invalid task ID {identifier!r}")
        if identifier != f"Q{int(identifier[1:]):03}" or identifier in seen:
            raise QueueError(f"duplicate or noncanonical task ID {identifier!r}")
        seen.add(identifier)
        if not normalized(row["task"]):
            raise QueueError(f"{identifier} has an empty title")
        if row["status"] not in STATES:
            raise QueueError(f"{identifier} has unknown status {row['status']!r}")
        if row["codex_task"]:
            link = re.fullmatch(r"\[[^\[\]\r\n]+\]\(codex://threads/([^\s)]+)\)", row["codex_task"])
            if not link:
                raise QueueError(f"{identifier} has an invalid Codex task link")
            row["codex_task"] = thread_url(link[1])
        if row["status"] in LINK_REQUIRED and not row["codex_task"]:
            raise QueueError(f"{identifier}: {row['status']!r} requires a Codex task link")
        if row["status"] in {"queued", "starting"} and row["codex_task"]:
            raise QueueError(f"{identifier}: {row['status']!r} cannot have a Codex task link")
        rows.append(row)
    return text[:begin], rows, text[end:]


def render(rows):
    table = [COLUMNS, ("---",) * len(COLUMNS)]
    for row in rows:
        values = [encode(row[key]) for key in KEYS]
        values[3] = f"[Open]({row['codex_task']})" if row["codex_task"] else ""
        table.append(values)
    return "\n" + "\n".join("| " + " | ".join(values) + " |" for values in table) + "\n"


def cells(line):
    parts = line.strip().split("|")
    if len(parts) != len(COLUMNS) + 2 or parts[0] or parts[-1]:
        raise QueueError("each queue table line must contain exactly five cells")
    return [part.strip() for part in parts[1:-1]]


def encode(value):
    value = html.escape(value, quote=True).replace("|", "&#124;")
    value = value.replace("\r", "&#13;").replace("\n", "&#10;")
    return re.sub(r"^\s+|\s+$", lambda match: "".join(f"&#{ord(c)};" for c in match[0]), value)


def normalized(title):
    return " ".join(title.split()).casefold()


def thread_url(identifier):
    try:
        return "codex://threads/" + str(UUID(identifier))
    except ValueError as error:
        raise QueueError(f"invalid thread UUID {identifier!r}") from error


def atomic_write(path, text):
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".TODO.", delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(text.encode("utf-8"))
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, path.stat().st_mode & 0o777)
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


if __name__ == "__main__":
    sys.exit(main())
