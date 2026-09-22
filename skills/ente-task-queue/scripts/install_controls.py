#!/usr/bin/env python3
"""Link the shared task controls into this host's Obsidian workflow vault."""

import fcntl
import json
from pathlib import Path

from queue import MACHINES, atomic_write, render_view


def main():
    root = Path(__file__).resolve().parents[3]
    config_file = root / ".workflow/local.json"
    with (root / ".workflow/sync.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        config = json.loads(config_file.read_text())
        if config.get("machine") not in MACHINES:
            raise ValueError("Configure this host's workflow sync first")
        source = root / "skills/ente-task-queue/obsidian"
        link = root / ".obsidian/plugins/ente-task-controls"
        if link.is_symlink() or link.exists():
            if not link.is_symlink() or link.resolve() != source:
                raise ValueError("Existing task controls belong to another installation; left unchanged")
        else:
            link.parent.mkdir(parents=True, exist_ok=True)
            link.symlink_to("../../skills/ente-task-queue/obsidian", target_is_directory=True)
        config["task_controls"] = True
        atomic_write(config_file, json.dumps(config, indent=2) + "\n")
        render_view(root)
    print("Linked task controls. Enable Ente task controls in Obsidian's Community plugins, then open TODO in Reading view.")


if __name__ == "__main__":
    main()
