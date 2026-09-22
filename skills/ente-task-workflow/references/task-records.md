# Task records that survive checkout deletion

## Reading order

Aman's starting point is the working Codex chat. State what happened, why it
matters, the recommendation or decision needed, and the next step there. A
finding left only in a file has not been communicated to him. Obsidian's daily
list needs only task name, status, machine tag and useful links.

PRD and BOARD are agent-maintained support, not mandatory reading. Keep the PRD
focused on the intended behavior, decisions and tests. BOARD starts with a short
current summary (about 60 words) and links, for example:

> **Waiting for your decision.** The dependency upgrade changes toast placement
> on older Android versions. The task chat explains the recommendation and choice.
> Next: resolve that choice before changing the dependency.
>
> Chat · PR (when present) · Plan · Claude review

Use real links, omit unavailable ones, and never invent a Claude session URL.
A saved Claude report is a useful link labeled **Claude review**; it is not a
link to the interactive CLI session. Keep the real session ID and resume context
in internal details. Use an actual session link only when verified.

After that summary, use Obsidian's native folded callout for agent metadata:
`> [!info]- Agent details`, with every content line (including blanks) quoted
with `>`. Raw HTML details around Markdown did not hide the body in Obsidian;
verify the actual reader, not just the file syntax.
Put exact host/project/checkout assignments, authorization sources and remaining
gates there or link to existing records containing them. Preserve the real
approval evidence and reviewed revisions; shortening the view does not change
permissions or erase proof. Keep hashes, commands and retry transcripts in
existing evidence/review records; link them instead of copying them into BOARD.
Update the current summary rather than appending successive status dumps.

Followups should name the user problem, why it matters, one evidence link and
whether it is merely proposed or explicitly queued. Use linked source lines or
PRs where helpful; routine commit hashes and machine bookkeeping do not belong
in that reading path. Keep supporting provenance in the linked evidence.

Resolve the host's records root and assigned repository from
[START-HERE.md](../../../START-HERE.md). The following is a laptop example;
on the mini use the assigned `ente` or `ente-2` checkout and its shared
`/Users/aman/Development/ente-workflow` records root.

For a task such as `B-photos-caption-save`, use:

- Checkout, created only after implementation approval:
  `/Users/amanraj/development/ente/.worktrees/B-photos-caption-save/`
- Lasting records, created while planning:
  `/Users/amanraj/development/ente-workflow/tasks/B-photos-caption-save/`

The lasting folder owns the ordinary files. Make the checkout's `.task` one
directory symlink to the entire lasting task folder. Do not use individual file
symlinks: editors that replace files can break them. A replace-and-rename write
through `.task/PRD.md` must still update the lasting PRD. Calculate the relative
target with `os.path.relpath` or use the full absolute path; Ente is nested one
level deeper than the shared records folder. Verify the resolved target exactly.
The records are outside both the repository and its worktree container.

Put the verified Codex chat link near the top of PRD.md and BOARD.md, and retain
the same link in TODO.md. Link each completed Claude report there when useful;
keep long findings in the report and summarize actionable conclusions in chat.
For queued work, read it from that item's linked row;
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
| `BOARD.md` | Short current outcome and next step with chat/PR/review links; agent routing and approval references under collapsed details |
| `approvals/<revision>/` | Real PRD/design copies and their digests at approval/review boundaries; never overwrite older approvals |
| `evidence/<run>/` | Before/after screenshots, numbered actions, device/build details, test commands and logs |
| `reviews/` | Original reviewer findings, dispositions, reviewed commits and bot comment links/revisions |
| `followups.md` | Nearby bugs, UX proposals and refactors, with evidence and queue decisions |

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

These records survive checkout removal and re-cloning Ente. Synced plans and
review notes have private Git history; raw screenshots/logs/evidence stay on the
originating host and still need a separate backup. Obsidian can open them as
ordinary Markdown, but installing it is unnecessary for Codex or Claude to read
and maintain them.
