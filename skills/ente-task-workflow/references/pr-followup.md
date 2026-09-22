# PR feedback and completed-task cleanup

Shared records live at
`/Users/amanraj/development/ente-workflow/` and are local, not published.
The six-hour follow-ups use this location; read STATUS.md before manual or
scheduled follow-up work and honor any user-requested hold. Registering a PR does
not override a hold. Do not assume scheduling a job proves it ran.

## After PR creation

Record task ID, worktree, branch, head repository, target repository, PR URL/number,
base and reviewed head SHA. For an upstream promotion, explicitly record its fork
counterpart; titles and similar branches do not prove a pair. Attach the PR with
the app tool and add it to `tracked-prs.json`. Preserve older revisions.

Personal skills and a local PRD are not automatically available to GitHub's bot.
Include the necessary accepted behavior, intentional omissions and tradeoffs in
the minimal PR body or review-request comment that Aman approves; do not publish
private notes wholesale or reinstate repository AGENTS files for this purpose.

Aman says Codex review is enabled on both repositories. Inspect live review state
and monitor the current PR revision. Do not claim completion from that setting,
or post duplicate requests while automatic review is pending. If a manual review
is needed and authorized, `@codex review` is the documented trigger; record its
comment ID and head SHA. Never substitute `@codex` plus an implementation request.

## Learn from findings

Store original bot findings in `review-findings.jsonl`, keyed by repository and
comment/review ID, preserving edited revisions, source URL and reviewed SHA.
Read inline comments, review bodies and thread state; do not confuse a resolved
thread or a thumbs-up with proof of correctness. Retain unverified/rejected/
accepted-tradeoff/fixed dispositions rather than deleting inconvenient evidence.

Process all pending unverified revisions, even if a collection reports no newly
inserted rows. Write classifications through `pr_reviews.py --record-disposition`
using the exact revision ID, reason and evidence from the automation tool
reference. Never rewrite the ledger by hand: collection and classification must
use the same lock. Prior assessments and original claims stay preserved.

Validate against reachable behavior, the reviewed source and the approved PRD.
Old-history failures included reviewers reopening accepted policy and tests
enforcing rejected behavior. Therefore a repeated bot claim is not automatically
a new rule. A confirmed recurring problem can justify a focused test, executable
check or short skill change. Show the proposed invariant and a bad/good replay
before promoting it. Product fixes still require the approved task plan and
publication approval. Keep only validated durable lessons in personal memory,
using the supported memory-update note location; do not rewrite MEMORY.md.

The review job discovers Aman's recently updated PRs using at least a 24-hour
window and revisits tracked PRs for delayed feedback. Deduplicate overlapping
runs; inaccessible pages, API failures or incomplete pagination are unknown,
never “no findings.”

## Cleanup boundary

Cleanup is currently **audit-only**. The executable guard is implemented and
offline-tested; the first live audit and a deletion executor remain outstanding. The plan is at
`/Users/amanraj/development/ente-workflow/archive/workflow-setup/automation-plan.md`.
Do not enable deletion just because the scheduler ran successfully.

For automatic cleanup, require exact recorded pairing, refreshed upstream/fork
state, no newer fork work, no active/dependent slice, preserved notes and commits,
and a clean worktree. Dirty/untracked/ignored files or uncertain identity block
removal. A closed-but-unmerged upstream PR needs a decision; it is not evidence
that work is disposable. Never force-remove, delete main, remove another task's
worktree, or delete remote branches. Preserve the PRD, evidence and ledger first,
using [task-records.md](task-records.md); an archive link into the checkout is not
preservation. Records resolve outside the repository and every checkout.

Reference: [Codex GitHub reviews](https://learn.chatgpt.com/docs/third-party/github).

Commands and record schema: [automation tools](../../ente-workflow-checks/references/automation-tools.md).
