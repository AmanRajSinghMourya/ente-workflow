# Tasks

[Open the workflow discussion in Codex](codex://threads/01a0b92d-15fb-76a3-a3f1-194acf660e22)

Give Codex a job in its chat as usual. The agent adds it here automatically,
links that same chat, and keeps the plan and status updated. Obsidian displays
these same files. You approve the plan before a worktree or code changes.

For a job you want picked up separately, tell Codex or Claude **“Add this task: …”**.
Say **“save for later”** to hold it. Ordinary questions and follow-up messages
stay in their existing conversation.

Agents maintain this file through the [task-list skill](skills/ente-task-queue/SKILL.md).
Task plans, screenshots and reviews stay in `tasks/` after a worktree is removed.

<!-- queue:start -->
| ID | Task | Status | Codex task | Context |
| --- | --- | --- | --- | --- |
| Q001 | Investigate Auth macOS PIN keyboard input | done | [Open](codex://threads/01a0c780-9d6a-7a82-9dab-d92990604dc2) | Read-only investigation of macOS Auth 4.4.25 build 1072 PIN lock keyboard input report; user reports Windows keyboard input works. Determine expected behavior and source/history evidence without product or Git changes. |
<!-- queue:end -->

| Status | What it means |
| --- | --- |
| queued | Waiting for a Codex chat to pick it up. |
| starting | Codex is opening that chat. |
| planning | The agent is investigating and preparing the plan. |
| needs decision | Waiting for your answer or plan approval. |
| implementing | The agent is making and checking the approved changes. |
| ready for review | The work and evidence are ready for your review. |
| done | The agreed work is complete. |
| deferred | Saved for later; the agent will not start it. |
| blocked | Cannot continue; the chat explains what is missing. |

The agent maintains these statuses. Completed rows stay here with their chat links.
