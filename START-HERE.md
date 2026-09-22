# Your work

**[Open the task list →](TODO.md)**

Give Codex a job in its chat. That same chat gives you the findings, any decision
needed and the next step. Obsidian is your task list, with links back to the work.
Each task has one optional reading page, its PRD, with the current outcome,
decisions and next step. Agents maintain the PRD and all supporting records.
A one-line request in Codex chat is enough to start investigation; no template
or separate task form is needed.

[Workflow chat](codex://threads/01a0b92d-15fb-76a3-a3f1-194acf660e22) · [Task records](tasks/)

> [!info]- Agent setup and storage details
> [Skills](skills/) · [Workflow status](STATUS.md) · [Design decisions](design-log.md)
>
> ## Which checkout to use
>
> | Machine | Code checkout(s) | Shared task records and skills |
> | --- | --- | --- |
> | MacBook Air | `/Users/amanraj/development/ente` | `/Users/amanraj/development/ente-workflow` |
> | Aman's Mac mini | `/Users/aman/Development/ente`, `/Users/aman/Development/ente-2` | `/Users/aman/Development/ente-workflow` |
>
> Use the requested machine and checkout; match both the host and exact path in
> Codex's project list. Record that assignment in the agent's opening context and
> BOARD's internal details; avoid repeating it in the readable PRD or chat summary.
> Reuse it on retries. For a batch Aman asks to split on the mini,
> alternate new tasks between its two checkouts; leave already running tasks in
> place. Each implementation gets its own worktree under its assigned checkout's
> `.worktrees/`. Both mini checkouts use the same mini TODO and records folder.
> Skills and task notes synchronize through the private `ente-workflow` GitHub
> repository after host setup. The daily TODO combines both machines; each agent
> updates its own machine's queue using the helper. Sync does not move work between
> machines or start remote tasks. [Sync help](skills/ente-workflow-sync/SKILL.md).
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
> the missing capability.
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
> unmeasured behavior works. On 22 September Aman authorized starting only the Mac
> mini's five-package SwiftPM pickup now. The MacBook Air's pickup is paused. Review
> collection and cleanup have not been brought forward; see [status](STATUS.md).
