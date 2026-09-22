---
name: ente-workflow-sync
description: Synchronize the private Ente task notes and personal skills between Aman's Macs, or diagnose a stopped sync. Use after shared skill changes or when the other Mac shows stale workflow notes.
---

# Shared workflow sync

Use the installed helper on the current host:

```sh
python3 -B ~/.codex/skills/ente-workflow-sync/scripts/sync.py sync
```

The same command is available through `~/.claude/skills/`. Its resolved location
finds the host's workflow folder; `.workflow/local.json` identifies the machine,
expected origin URL and personal skill-link directories. That configuration,
credentials, schedules and app settings stay local. See [START-HERE.md](../../START-HERE.md)
for the two hosts and code checkouts.

Aman authorized automatic commits and ordinary pushes in the private
`AmanRajSinghMourya/ente-workflow` repository, including skill additions,
updates and removals. This exception applies only to this workflow repository;
Ente product commits, PRs and implementation keep their own approval boundaries.
Do not grant another account access or transfer credentials without permission.

The helper commits eligible local notes/skills, fetches and merges main, repairs
only its own skill links, regenerates the combined task list, and pushes normally.
An installed macOS LaunchAgent runs it every five minutes while logged in; run it
at handoff after a shared skill change for immediate delivery. Obsidian need not
be open. GitHub Actions and model calls are not involved.

Use `queue.py` for task state. It writes only this host's queue and shares the
sync lock. The generated TODO is a readable list, never the mutation source.
Read `list --all` to inspect both hosts. IDs are local to each machine; preserve
the existing Codex chat and task folder. Sync does not dispatch remote tasks.

## When sync stops

Read `.workflow/sync-status.json` and the actual Git status. Offline or rejected
pushes retain local commits for the next retry. A conflict preserves both sides
and blocks queue changes. Resolve the actual conflicting intent before finishing
the merge; never silently choose one side, reset, force-push, stash user work or
remove files to make sync appear successful. Pre-staged user changes and non-main
branches stop automatic sync. `links` repairs links only; it does not prove a sync.

Credential filename/pattern and size checks reduce accidental uploads; they are
not proof that arbitrary private content is safe to share. Keep credentials out
of this folder. Raw evidence and logs are local; linked reports may require the
originating host. The private repository is a history of notes and skills, not an
Ente code backup or a complete device-evidence backup.

For a new host, reconcile its existing notes and skills before installing a
clone; do not overwrite it with another machine's older snapshot. Verify the
repository is private using authenticated `gh`, and verify both fetch/push URLs.
Use `scripts/install_service.py` only after `.workflow/local.json` and ordinary
manual sync work. Validate changes with `scripts/test_sync.py` (temporary local
Git remotes only) and the queue/collector replay tests.
