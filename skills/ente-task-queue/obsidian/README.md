# Task controls

Checkboxes mark tasks done; unchecking returns them to Review. Click the status
chip for Needs you, Review, Later or Blocked. Filters narrow the list. Chat holds
the findings and next step; PRD is the single optional task-reading page. PRD
and PR links appear when those records exist. Detailed agent records stay out
of this list.

Status changes save through `queue.py`. They do not approve code, open PRs or
dispatch work. Imported historical tasks may still be readable here; this is not a live view of the other Mac.

## Install on each Mac

After this host's `.workflow/local.json` identifies its machine, run:

```sh
python3 -B ~/.codex/skills/ente-task-queue/scripts/install_controls.py
```

In Obsidian's workflow vault, enable **Ente task controls** under Community
plugins. Open TODO in Reading view. Confirm the local extension's access before
first enabling it. The installer preserves other plugins and does not change
Obsidian's trust settings.

The extension links to this folder; Git can distribute its source. Obsidian settings
and activation stay local. After a source update, reload the extension to use it.
When controls are enabled, TODO contains only the interactive task panel. There
is no duplicate fallback box. Hosts configured without controls use a plain
Markdown list instead.
Task lists and records are not synchronized; the five-minute file sync is retired.
