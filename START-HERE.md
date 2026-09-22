# Your work

**[Open the task list →](TODO.md)**

Drop a one-line task in **todos** on the Mac where it should run:
[MacBook Air](codex://threads/01a0c925-2578-7972-a1ed-821b273e5b49) ·
[Mac mini](codex://threads/01a0c925-66f8-7f13-b219-19b3f1d3d06a).

Tasks from these chats enter that Mac's list. Other chats enter TODO only when
you explicitly ask; ordinary questions and investigations stay outside it.
The working chat gives you findings, decisions and next steps. Each task has one
optional reading page, its PRD. Agents maintain the supporting notes.

[Workflow chat](codex://threads/01a0b92d-15fb-76a3-a3f1-194acf660e22)

> [!info]- Agent setup and storage details
> [Skills](skills/) · [Workflow status](STATUS.md) · [Design decisions](design-log.md)
>
> ## Which checkout to use
>
> | Machine | Code checkout | Local task records and personal skills |
> | --- | --- | --- |
> | MacBook Air | `/Users/amanraj/development/ente` | `/Users/amanraj/development/ente-workflow` |
> | Aman's Mac mini | `/Users/aman/Development/ente` | `/Users/aman/Development/ente-workflow` |
>
> Posting in a machine-specific `todos` chat selects that Mac for the task and
> its notes. Otherwise ask if the machine is unspecified. Match host and path in
> Codex's project list. Record that assignment in the agent's opening context and
> BOARD's internal details; avoid repeating it in the readable PRD or chat summary.
> Each machine has one main checkout. On the mini, new planning tasks use
> `/Users/aman/Development/ente`; implementation uses a separate task worktree
> under its `.worktrees/` after the applicable plan approval. Do not create a
> second clone or alternate between checkouts. Reuse the task's assignment on
> retries. Historical records can retain the paths where old work happened.
> Skills and workflow instructions are distributed through the private
> `ente-workflow` Git repository. TODO, queues, plans and reviews stay local for now;
> neither Git updates nor note edits dispatch work on the other machine.
> The old five-minute file sync is retired on both Macs. Wait for Aman's new
> agent distribution details; do not recreate it. [Distribution](skills/ente-workflow-sync/SKILL.md).
>
> ## Where everything lives
>
> Use the records folder for this host from the table above. Obsidian is a reader
> for these ordinary files. Codex and Claude can also read and update them directly.
>
> `skills/` is the single home for our personal skills and their scripts. Both
> `~/.codex/skills/` and `~/.claude/skills/` link here. Vendor-managed system and
> plugin packs stay with their installers. Sharing instructions does not give an
> agent tools that only exist in the other app; use available equivalents or report
> the missing capability. For Ente, existing code patterns take precedence over
> generic Dart/Flutter tutorials. A skill does not authorize a new dependency,
> router or architecture. The personal Sentry CLI skill is retired here because
> that CLI is unavailable; vendor-managed integrations remain separate.
>
> `tasks/<task-name>/` holds the PRD, decisions, tests, screenshots and reviews.
> After you approve implementation, the checkout goes under Ente's `.worktrees/`,
> for example `B-photos-caption-save`, branch `aman/photos-caption-save`. Its `.task`
> is one directory link to the lasting task folder here. There is no second copy.
>
> The old setup records are in [archive/workflow-setup](archive/workflow-setup/).
> These host-local records preserve how the tools were built and tested, so we can investigate an old
> decision or a problem with this setup. Agents consult them only for that history;
> they do not run anything or enter normal task context. `tasks/` holds each job's
> own plan and results. The agent maintains these records; you need only the chat
> and task list.
>
> Nearby discoveries are offered for the task list and get their own approval.
> Personal checks stay in these skills; they are not Ente tooling PRs or proof that
> unmeasured behavior works. Aman has abandoned the old Mac mini task batch;
> historical pilot authorization must not restart it. Start from current requests.
> Existing schedules keep their configured status unless Aman changes them;
> see [status](STATUS.md).
