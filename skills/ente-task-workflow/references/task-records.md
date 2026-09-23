# Task records that survive checkout deletion

## Reading order

Aman's starting point is the working Codex chat. Both it and PRD.md should read
like a short newspaper article: the main point first, then connected paragraphs
that add the context needed to understand it. Write for a teammate who has not
seen the TODO prompt and may not be an engineer. Use this reading sequence as
guidance, not a questionnaire or a set of labels to print:

1. Name the problem or outcome and its practical impact in one or two sentences.
   Surface an urgent decision or verification gap here rather than burying it.
2. Explain the current behavior with a concrete example when useful. Introduce
   the component or unfamiliar term before explaining what went wrong. Separate
   an observed cause from a hypothesis; do not invent why old code was written.
3. Explain the proposed or completed change and why it addresses the problem.
   Describe the relevant mechanism in plain language, including material tradeoffs
   or intentionally preserved behavior. Keep planned work distinct from done work.
4. Say what the checks and reviews actually established and what remains untested
   or disputed. Translate a finding into its consequence; summarize its disposition
   here so the reader need not open the full review to understand the outcome.
5. Finish with the current state, any choice Aman must make and the next action.
   A PR being open, local tests passing and GitHub CI passing are different facts.

Prefer a descriptive title and a few short paragraphs. Each paragraph should
build on information already introduced. Short headings, a small diagram or an
analogy can help a complex explanation; they are optional. An analogy or joke
must clarify the actual mechanism, not replace it. Avoid jargon, status-field
stacks, command inventories and narration of every tool call. Keep one name for
each concept. Do not expand a simple task to fill a template or turn the PRD into
a tutorial. A short task usually needs only a few hundred words; the existing
50,000-byte maximum is a ceiling, not a target.

The first task message explains the problem and approach in the working chat.
Later updates cover meaningful discoveries, changed decisions, review conclusions
and blockers. The final reply gives a self-contained account of the outcome and
remaining work, even if earlier updates are collapsed. Sending a completion report
only to the TODO coordinator does not satisfy this requirement. PRD.md preserves
the same explanation; update its current story rather than append status dumps.
Obsidian's daily list remains a compact index, not a second article.

Put links beside the claim they support or in a compact reading-links row after
the opening. The explanation must still make sense without following any link.
Link completed Codex/Claude review reports from the PRD and final handoff; state
their consequential findings in the text. Use an actual conversation link only
when verified. A saved CLI report or session ID is not a browser chat URL; keep
resume details in the supporting notes and disclose unavailable sessions honestly.

Before sending, read the opening straight through with links and internal details
ignored. Can a new reader explain the problem, the change, the evidence/gaps and
what happens next? Fix missing context or unexplained terms. A heading/word-count
script cannot establish comprehension; this is an editorial check.

This adapts the explanatory approach in Cursor's
[teach skill](https://github.com/cursor/plugins/blob/main/pstack/skills/teach/SKILL.md).
Use its plain account of what, how and why. This workflow does not install that
skill or depend on its `how`, `why` or `unslop` skills, extra agents or images.

A one-line request in Codex chat is sufficient intake. The agent investigates
code and existing records to develop behavior, scope and acceptance examples,
then asks only about real remaining gaps or decisions. Templates guide the agent;
never ask Aman to fill one or maintain these records himself.

BOARD and detailed review/evidence files remain agent-maintained support. Keep
routing, approval provenance, reviewed revisions and session resume information
there. Preserve existing files and approval evidence. Use real links, omit
unavailable ones, and never invent a Claude session URL. Summarize review
conclusions in PRD and chat; retain original reports in the supporting records.

In BOARD, use Obsidian's native folded callout for agent metadata:
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
on the mini use `/Users/aman/Development/ente` as the single main checkout,
its `.worktrees/` for approved implementation, and
`/Users/aman/Development/ente-workflow` as the shared records root.

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

Put the verified Codex chat link after the opening of PRD.md and near the top of
BOARD.md, and retain the same link in TODO.md. Include completed reviewer report
links in the PRD and final chat handoff, with internal session details in BOARD;
keep long findings in the reports and explain their consequences in PRD and chat.
For queued work, read it from that item's linked row;
for an existing app task, verify the task ID through the app. If work has no Codex
chat yet, say so instead of fabricating a link.

Start with PRD.md and the short BOARD.md. Add the other files only when that task
produces the corresponding design work, evidence or review. Do not copy the setup
archive or historical instruction backups into new tasks or their opening prompts.

Keep these files only when they carry useful information:

| File in the lasting folder | Contents |
| --- | --- |
| `PRD.md` | Single optional reading page: current outcome, intended behavior, decisions, next step, Chat/PR links and testing/review conclusions; at most 50,000 UTF-8 bytes |
| `design.md` | Optional supporting diagrams, Figma links, alternatives and baseline screenshots; required decisions remain in the PRD |
| `BOARD.md` | Agent continuity, routing, approval references and detailed report links under collapsed details |
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
