---
name: ente-task-workflow
description: Take an Ente bug, feature, migration, or improvement from code exploration and a concise PRD through small implementation slices, tests, independent Codex and Claude reviews, and Aman-approved commits and PRs. Use for implementation tasks, not standalone investigation or review.
---

# Ente task workflow

The working chat is Aman's primary reading surface. Lead with the outcome or
problem and its user impact, then the recommendation/decision needed and next
step. Link the PR and PRD when useful. Obsidian exposes the compact TODO and
one optional reading page per task: PRD.md. Put the current outcome, decisions,
next step and brief testing/review conclusions there. BOARD, evidence and raw
reviews remain agent-maintained support, not another reading path.
A one-line request in Codex chat is enough to begin: expand it through code
investigation and ask only about real gaps that sources cannot resolve. Never
require Aman to fill a template or use a separate intake form. Use the reading order in
[task-records.md](references/task-records.md); keep paths, hashes, IDs, approval
provenance and command logs out of routine user-facing summaries.
Read the current task and personal `~/.codex/AGENTS.md` first. Do not create or
rely on repository AGENTS files for this workflow. This
skill coordinates work; it does not authorize commits or publish anything itself.

The approval gates and review order below are defaults. Aman's explicit current
authorization for a named task or batch takes precedence within its stated scope.
Record the actual message/source, allowed actions and remaining decision gates in
the PRD and task brief. Do not demand an approval already supplied, extend the
exception to other work, or treat an unverified file claim as user authorization.

TODO intake is opt-in outside the dedicated `todos` chats. Use `$ente-task-queue`
only for tasks submitted there, an explicit add-to-TODO request elsewhere, or an
existing queue entry. Do not automatically register a direct task, investigation
or question. Work launched from the queue keeps its existing row and chat link;
maintain its status as approved work proceeds. Keep the PRD/BOARD current for
implementation continuity even when the task is not listed in TODO. A status
label never substitutes for an approval message.

## Understand and plan before editing product code

1. Inspect the relevant code, tests and analogous implementations. Existing Ente
   navigation, network clients, architecture and test conventions take precedence
   over generic Dart/Flutter tutorials. Do not add a package or replace an existing
   pattern merely because a skill uses it. Verify required tools are available.
   For design,
   UI/UX or Figma requests, first load `$ente-design-decisions`; it checks the
   design team's in-flight work and existing precedents. Resolve facts
   from those sources before asking Aman. For a remaining product/design choice
   or material uncertainty, use the Codex/Claude planning consultation in
   [references/reviews.md](references/reviews.md), then bring Aman the recommendation
   and any disagreement. Continue independent work while waiting, but do not
   implement an unanswered choice or silently reopen accepted answers.
2. Create a short PRD from [assets/PRD.md](assets/PRD.md). Record behavior to preserve,
   acceptance examples, exclusions, affected paths, design decisions and executable
   slices. For migrations, explain whether the existing pattern is sound. Compare
   material alternatives when it is not; use a fresh Claude planning opinion via
   [references/reviews.md](references/reviews.md) when alternatives need comparison.
   List unrelated older implementations as follow-ups, not automatic refactors.
3. Keep the PRD at most **50,000 UTF-8 bytes**, usually much smaller. Explanations can
   stay in chat; decisions and acceptance criteria needed to implement/review must
   stay in the PRD. Split an oversized feature instead of hiding requirements.
4. Split by independently reviewable behavior and dependencies before coding.
   Estimate files and change size per slice; aim below **500 added/deleted lines**.
   Exact size is unknowable before implementation. Measure as work progresses;
   **over 1,000 lines requires stopping and re-planning/splitting**, unless Aman
   explicitly approves a documented exception. Tests and generated text count.
   Report binary changes separately. Do not pad or split work to inflate PR counts.

## Approval, worktree and shared notes

Present the PRD/plan and proposed design in chat. **Wait for Aman to approve that
plan and authorize implementation before creating a branch/worktree or editing
product code.** Reading source, investigating and drafting the plan are allowed.
Record the actual approval message/reference; never manufacture approval in a file.
If a later finding changes an accepted product/design decision, return that decision
for approval before implementing it. Do not add permission gates to ordinary reads.

Resolve the host and assigned checkout from the shared root's
[START-HERE.md](../../START-HERE.md), and record both in BOARD's internal details.
Use the same assignment through implementation and review; do not repeat machine
routing boilerplate in the PRD or the human-facing summary. Each Mac has one
primary Ente checkout and local task records; never use the laptop's paths on the
mini. Ask which machine to use when Aman has not specified it for a new task.

After approval, fetch current main, check the approved plan still fits that source,
and create a short `aman/<surface>-<task>` branch with its checkout directly under
the assigned repository's `.worktrees/`. Each task has its own worktree; do not
edit product files or switch branches in the primary shared checkout. Use a readable directory name:
`B-photos-caption-save` for a bug, `F-photos-album-sharing` for a feature, or
`I-photos-share-dialog` for an improvement. Include the surface (photos, auth,
locker, server or infra) in every new task folder and the corresponding branch;
for example `aman/photos-caption-save`. Naming helps orientation but does not
replace checking actual Git/PR identity. Use hyphens, not spaces/quotes. Continue an existing task in its
existing worktree. Aman's requested limit of eight is only the app's managed
worktree retention setting; it is not a limit on active tasks or agents. Its
current setting must be verified in the app, not inferred from this instruction.

Keep the lasting task folder outside the repository from the start, using
[references/task-records.md](references/task-records.md). Make `<worktree>/.task`
one directory symlink to that folder. PRD.md, design.md, BOARD.md, reviews and
followups then remain visible beside the diff without a second copy. Compute the
link target from the actual directories; do not guess its relative depth.
Open `.task/PRD.md` alongside the diff. Exclude the symlink using the narrow
`/.task` entry in Git's local exclude file; a trailing slash would only match a
directory and can fail to exclude this symlink. Do not add repository instructions.
Because excluded notes are absent from the code fingerprint, always check the PRD's
separate digest during review. Record base SHA, approval, current slice, dependencies,
blockers and next action. The acting agent maintains these notes; Aman should not have to.

Use the current host's `ente-workflow/tasks/<task-name>/` folder (START-HERE.md) for
review logs, validation receipts and preserved task notes outside the checkout.
Draft plans can live there before worktree approval. Both CLIs read these ordinary
files; no notes application is required. A link back into a deletable checkout is
not an archive. The records folder is a sibling of the repository and survives
checkout removal or a re-clone of Ente.

For multiple PRs, use the same worktree sequentially with one writer. Switch
branches only after approved commits and no unfinished code changes. A dependent
slice branches from its predecessor and records that PR dependency; an independent
slice starts from current main. Do not stash/rebase Aman’s work silently. An open
or planned dependent slice keeps the worktree in use even if one PR has merged.

## Implement and verify each slice

Use `$ente-workflow-checks` and its personal `scripts/README.md`. There is one
shared installation, reachable at `~/.codex/skills/ente-workflow-checks/scripts/`
and the equivalent Claude skill link. Always pass the actual task checkout as
`--repo`. Never copy these tools into Ente or prepare tooling PRs. If a helper is
missing, report that gap. Run
`check_task.py prd` before implementation and after requirement changes, and
`check_task.py diff` with the recorded base during implementation and before review.
These commands check document bytes/freshness and actual change size, not quality.

- For a bug: first write a focused test, observe the failure caused by that bug,
  keep its expected behavior fixed, implement the fix, rerun the **same test**.
  Save red and green outputs. A missing SDK/import or broken fixture is not a bug
  reproduction. If there is no reliable automated reproduction, explain the gap
  and agree on the verification approach before calling the bug fixed.
- For features/migrations: derive tests from the PRD's acceptance examples and
  exercise them before implementing the new behavior where feasible. For
  migrations also preserve old data/API behavior or specify the intended change.
  Documentation-only changes need their applicable checks, not fabricated tests.
- Link important tests to the approved acceptance examples. Historical caption
  tests passed while expecting a save-on-dispose behavior Aman had rejected: a
  green test is useful only if its expectation is right. When Aman corrects the
  same behavior repeatedly, preserve the accepted behavior in a regression test
  if observable. Use a script for mechanical constraints and
  a decision note for product judgment; not every correction can become a script.
- For UI, follow `$ente-design-decisions` and select useful widget/interaction
  tests. Golden baseline policy remains undecided; agree on it when relevant.
  Read Figma through its skill when needed; do not write to the team's Figma file
  without an explicit user instruction. Do not auto-update goldens or claim visual
  correctness from a logic test.
- During mobile verification, use computer control of the simulator for the
  affected user journey where available. Capture the bug on the unchanged build
  before the fix and repeat the same journey afterward; record missing baseline
  evidence honestly. Use `$ente-ui-observer` for a separate agent to inspect saved
  screenshots and interaction notes while the parent alone operates the simulator.
  This agent verification happens before final code approval; the post-PR simulator
  question below is Aman's own walkthrough. Respect a task-specific instruction
  that Aman will handle simulator verification himself.
  For login, reuse the dedicated test account in this host's
  `~/.config/ente-workflow/mobile-test-account.json` (`email`, `password`). Aman
  authorizes its use for mobile verification without repeated approval. Keep the
  credential file local with mode 0600; share its path, not its contents, with
  reviewers or other tasks. Do not put credentials in Git or task evidence.
  Handle iOS Simulator lock screens without asking Aman to unlock them. Identify
  whether it is the simulator device lock or Ente's app lock. Use supported
  simulator controls, a recorded test PIN, or configured simulated biometrics;
  the account password is not an assumed device passcode or app PIN. If an unknown
  app PIN blocks ordinary feature testing, use a separate disposable simulator
  instead of erasing the existing device or resetting the account. Lock/privacy
  regression tests must retain their actual reproduction state; report a concrete
  blocker if that state cannot be recovered and do not claim verification passed.
  This simulator rule does not authorize unlocking the Mac host itself.
- After the code shape settles, format and run the relevant repository CI checks.
  Save command evidence outside the checkout with `checks.py run`; verify it again
  before relying on it. Focused red tests are the exception to delaying broad runs.

When root-cause investigation stalls after a concrete attempt, ask a fresh Claude
CLI session for independent findings with the reproduction, source paths, ruled-out
hypotheses and missing evidence. Keep it read-only and use the custom prompt pattern
in the review reference. A second opinion is a hypothesis until verified.

## Return discoveries to the planning queue

Record related bugs, confusing flows and refactor opportunities as they arise in
the durable task's `followups.md`, with evidence and a clear distinction between
observed behavior and a proposed improvement. While an observer batch is active,
it owns writes to that file; merge the parent's discoveries after it returns.
Keep unrelated changes out of the current implementation. At completion, show a
short deduplicated list and offer
to add selected items to this host's TODO using the queue helper
or leave them in the task record. Adding to TODO authorizes investigation/planning,
not implementation; each item returns through the normal plan/design approval.
A defect in the current change or an unmet acceptance criterion still belongs in
the current task and must be addressed or disclosed before requesting approval.

## Independent reviews and publication approval

Once the slice is stable, follow [references/reviews.md](references/reviews.md) to
run fresh **Codex CLI and Claude CLI** reviews of the same PRD, base, exact change
and evidence. Use custom prompts, never Claude `/code-review`. Neither reviewer
edits code. Record all findings and the primary agent's source-grounded disposition:
confirmed, rejected with reason, or needs Aman’s decision. Do not treat agreement
between models as proof. A user-pasted Claude review remains classification-only
unless Aman authorizes edits.

Fix confirmed issues within the agreed task, preserving the original findings and
their dispositions. Ask about changes that require a new product decision or
expand scope. Refresh affected tests and both reviews for changed code/requirements.
Do not run an unbounded review loop: after two fix/review rounds, report remaining
disagreements for Aman’s decision.

When ready, present one approval request containing:

- What changed, all findings with their dispositions, test evidence and gaps.
- Logical commit groups and proposed messages, with tests beside their behavior.
- Exact PR destination, head repository/branch, API account, base branch, title
  and optional minimal body. Default to `AmanRajSinghMourya/ente`; use
  `ente-io/ente` when Aman selects it. Inspect existing PR identity before updates;
  never infer destination from the branch name or Git commit author.

Ask whether to make **those commits and open that PR**. General task approval, a
green check, a review, or a file saying “approved” is not publication approval.
Do not stage or commit before Aman approves. If the reviewed content changes,
refresh the proposal and obtain approval for the changed content.

After approval, verify evidence still matches, follow current identity/PR rules,
commit the agreed groups, and verify the committed tree matches the reviewed
files. The commit changes HEAD: old `checks.py verify` receipts will be stale;
record the tree comparison or rerun required checks before claiming coverage of
the new commit. Push and create the PR with authenticated `gh`, attach it to the
task, and fire the requested confetti once. Register the PR, reviewed SHA, task and
worktree with the persistent review ledger. Follow
[references/pr-followup.md](references/pr-followup.md) for bot review monitoring,
validated lessons and cleanup. For mobile changes, ask:
**“Should I start the simulator so you can verify the changes?”** Wait for the answer.

Skills guide the agent. These checks enforce their own comparisons when invoked;
they are not an installed global hook, CI gate, or guarantee of bug-free code.
