# Task records that survive checkout deletion

The working Codex chat is Aman's primary reading surface; Obsidian is primarily
a compact TODO. Agents maintain the supporting records without requiring Aman to
read them or copy decisions into them. Keep each task's own PRD; a batch PRD is a
reference, not a replacement for the package's plan.

Start BOARD.md with about 60 words covering the current outcome or problem, user
impact, recommendation or single decision needed, and next action. Follow with
the actual Codex chat, PR when one exists, and saved Claude review links. Keep
exact paths, queue/host/project IDs, approval provenance, hashes, raw review
commands and model settings in existing internal records or a collapsed technical
section. In Obsidian use a folded callout (`> [!info]- Technical details`), with
each history line quoted inside it; an HTML details wrapper can leave Markdown
history visible outside the fold. Preserve old history and review evidence; presentation changes do not
change approval scope or make historical checks current.

Link a Claude session URL only when it exists and has been verified. Otherwise
label the saved report link **Claude review** and retain the real resumable session
ID in internal notes. Do not invent a Claude chat URL. Chat updates use the same
outcome-first order and a few useful links, without routine hash dumps.

For a task such as `B-photos-caption-save`, use:

- Checkout, created only after implementation approval:
  `<assigned-checkout>/.worktrees/B-photos-caption-save/`
- Lasting records, created while planning:
  `/Users/aman/Development/ente-workflow/tasks/B-photos-caption-save/`

Resolve the assigned checkout from the actual host and `list_projects`, then
persist its host, project ID and path in PRD/BOARD before dispatch. On the source
laptop, use `/Users/amanraj/development/ente`. On this Mac mini, the available roots
are `/Users/aman/Development/ente` and `/Users/aman/Development/ente-2`; both use
the single shared TODO and records folder. For an explicitly split batch, alternate
the two mini roots in queue order and persist the assignments before the first
claim. Reuse those assignments on retries and follow-ups. Continue running tasks
in their assigned checkout/worktree; never move them to rebalance the batch.

Record the assigned checkout, host and project ID in the PRD and BOARD's internal
technical details. Worktree creation must use that checkout, not whichever project is
currently focused in the app.

The lasting folder owns the ordinary files. Make the checkout's `.task` one
directory symlink to the entire lasting task folder. Do not use individual file
symlinks: editors that replace files can break them. A replace-and-rename write
through `.task/PRD.md` must still update the lasting PRD. Calculate the relative
target with `os.path.relpath` or use the full absolute path; Ente is nested one
level deeper than the shared records folder. Verify the resolved target exactly.
The records are outside both the repository and its worktree container.

Put the verified Codex chat link near the top of PRD.md and BOARD.md, and retain
the same link in TODO.md. For queued work, read it from that item's linked row;
for an existing app task, verify the task ID through the app. If work has no Codex
chat yet, say so instead of fabricating a link.

Start with PRD.md and the short BOARD.md. Add the other files only when that task
produces the corresponding design work, evidence or review. Do not copy the setup
archive or historical instruction backups into new tasks or their opening prompts.

Keep these files only when they carry useful information:

| File in the lasting folder | Contents |
| --- | --- |
| `PRD.md` | Current plan, accepted behavior and tests; at most 50,000 UTF-8 bytes |
| `design.md` | Optional supporting diagrams, Figma links, alternatives and baseline screenshots; required decisions remain in the PRD |
| `BOARD.md` | Brief current outcome and next action first, then chat/PR/review links; technical details and preserved history collapsed |
| `approvals/<revision>/` | Real PRD/design copies and their digests at approval/review boundaries; never overwrite older approvals |
| `evidence/<run>/` | Before/after screenshots, numbered actions, device/build details, test commands and logs |
| `reviews/` | Original reviewer findings, dispositions, reviewed commits and bot comment links/revisions |
| `followups.md` | User problem, why it matters and source link for nearby bugs, UX proposals and refactors; evidence and queue decisions retained internally |

The acting agent maintains the records. Do not ask Aman to copy chat decisions into them.
File text saying "approved" is not authorization: cite the actual user response.
Revised requirements need an explicit new approval before they replace an accepted
decision. Keep review inputs and outputs as evidence for their original revision.

For simulator evidence, record the tested app, source SHA and uncommitted-change
fingerprint/build identity, device and OS, relevant locale/theme/text scale,
fixture/account role, timestamp, initial state, numbered actions and observed
result. Preserve before/after capture paths. Use a short recording when order or
timing matters; one screenshot cannot establish a whole interaction. Link actual
evidence in the PRD/design and final report. Do not call a recreated mockup a
baseline, or reset Aman's app data to get a clean screenshot.

Before cleanup, preserve the final PRD/design, approvals, evidence, review record,
commit/PR links and unresolved follow-ups here. Check that files can be read
without resolving any path through the checkout; missing evidence blocks cleanup.
Unknown or unpreserved ignored files still block cleanup. The cleanup guard
may recognize only the single `.task` directory link after proving its exact
lasting target; an ordinary directory or another target is not equivalent.

These local records survive checkout removal and re-cloning Ente; they are not
a backup against deleting this separate folder or losing the disk. Obsidian can open them as
ordinary Markdown, but installing it is unnecessary for Codex or Claude to read
and maintain them.
