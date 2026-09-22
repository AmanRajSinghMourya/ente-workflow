# Task controls

Checkboxes mark tasks done; unchecking returns them to Review. Click the status
chip for Needs you, Review, Later or Blocked. Filters narrow the list. Chat holds
the findings and next step; Plan and PR links appear when those records exist.

Status changes save through `queue.py`. They do not approve code, open PRs or
dispatch work. The other Mac's tasks are readable here; update them in their chat.

## Install on each Mac

After workflow sync is configured, run:

```sh
python3 -B ~/.codex/skills/ente-task-queue/scripts/install_controls.py
```

In Obsidian's workflow vault, enable **Ente task controls** under Community
plugins. Open TODO in Reading view. Confirm the local extension's access before
first enabling it. The installer preserves other plugins and does not change
Obsidian's trust settings.

The extension links to this folder; Git synchronizes its source. Obsidian settings
and the host's activation flag stay local. After a source update, reload the
extension to use it. Hosts without it retain the plain Markdown task list.
