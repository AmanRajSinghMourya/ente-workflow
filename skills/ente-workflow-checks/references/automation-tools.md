# Review collection and cleanup audit

Both tools use Python 3.9+, the standard library, Git and authenticated `gh`.
Request the normal elevated permission for live `gh` calls. Check `STATUS.md`
and `control.json` first. A future `not_before` returns `held` before any API call.
Do not move that date earlier to run a test; use the offline fixtures instead.

## Collect bot reviews

```sh
python3 -B ~/.codex/skills/ente-workflow-checks/scripts/pr_reviews.py
```

The collector discovers recently updated author PRs and revisits every tracked or
previously observed PR. It verifies the account and bot identity, follows all
pages, saves raw responses and appends new comment revisions without rewriting
old classifications. All collector/classification writers use the same lock.
`review-state.json` stores the last successful cutoff and
current PR/thread snapshots. A finding's `current_head` is the head seen at its
`observed_at` timestamp and stays historical with that revision; use the latest
`review-state.json` PR head (or refresh GitHub) when judging the current code.
Legacy imported rows retain their original fields; use the retained sample/raw
responses for their provenance. `review-findings.jsonl` keeps original claims.
`raw/review-runs/` retains source responses. An incomplete run does not advance
the cutoff. Process every `pending_ids` entry, even when `new_count` is zero:
those are unverified revisions, including findings saved by an interrupted run.
Exit 0 means collection completed or was held, not that bot findings
were validated. Exit 2 means incomplete. Inspect the JSON status.

## Save a finding's classification

Never rewrite `review-findings.jsonl` by hand. After checking the actual claim,
save this payload in a task evidence file. Copy the complete revision array from
`pending_ids`; do not rebuild it from a PR number or current head:

```json
{"revision":["REPO","KIND",123,"UPDATED_AT","CONTENT_DIGEST"],
 "disposition":"confirmed", "reason":"Source-grounded assessment",
 "evidence":["Actual source or reproduction reference"]}
```

```sh
python3 -B ~/.codex/skills/ente-workflow-checks/scripts/pr_reviews.py --record-disposition /absolute/assessment.json
```

The same requested hold applies to classification: before `not_before`, the
command returns JSON status `held` with exit 0 and writes no classification.
Always inspect JSON status; exit 0 alone does not mean a write occurred.
Allowed dispositions are unverified, confirmed, rejected, accepted-tradeoff and
fixed. The command takes the collector's lock, matches one exact revision and
preserves assessment history and original finding fields. Busy, stale or invalid
input is incomplete; retry after reading current state. A valid saved assessment
does not prove its human/model judgment correct. Do not mark an unresolved claim
rejected merely to empty the pending list.

## Audit cleanup eligibility

```sh
python3 -B ~/.codex/skills/ente-workflow-checks/scripts/cleanup_guard.py --repo /absolute/assigned/ente --records-root /absolute/host/ente-workflow --activity-evidence /absolute/fresh-activity.json
```

Save stdout in the task's evidence folder. `control.json.cleanup_mode` must be
`audit`. This tool has no mutation option; every output says
`mutation_authorized: false`. Per-task states are eligible, blocked or unknown.
Overall exit 2/status incomplete means evidence is missing or invalid; exit 0
can still contain blocked tasks or no candidates. Never infer deletion approval.

### Registration schema

`tracked-prs.json` starts as `{"version":1,"tasks":[]}`. Each complete cleanup
registration requires the following fields (replace every example from verified
task/PR records; the examples do not authorize anything):

```json
{
  "id": "B-photos-caption-save",
  "worktree": "/Users/amanraj/development/ente/.worktrees/B-photos-caption-save",
  "branch": "aman/photos-caption-save",
  "head_sha": "FULL_VERIFIED_SHA",
  "status": "completed",
  "thread_ids": ["ACTUAL_THREAD_ID"],
  "depends_on": [],
  "prs": [
    {"repo":"AmanRajSinghMourya/ente","number":1},
    {"repo":"ente-io/ente","number":2}
  ],
  "fork": {"repo":"AmanRajSinghMourya/ente","number":1,"head_repo":"AmanRajSinghMourya/ente","head_branch":"aman/photos-caption-save","head_sha":"FULL_VERIFIED_SHA","base":"main"},
  "upstream": {"repo":"ente-io/ente","number":2,"head_repo":"AmanRajSinghMourya/ente","head_branch":"aman/photos-caption-save","head_sha":"FULL_VERIFIED_SHA","base":"main"},
  "mapping_evidence": "ACTUAL_PAIRING_SOURCE_REFERENCE",
  "archive": {
    "path":"/Users/amanraj/development/ente-workflow/tasks/B-photos-caption-save",
    "files":[
      {"path":"PRD.md","sha256":"ACTUAL_DIGEST"},
      {"path":"BOARD.md","sha256":"ACTUAL_DIGEST"},
      {"path":"reviews/findings.md","sha256":"ACTUAL_DIGEST"},
      {"path":"commits.bundle","sha256":"ACTUAL_DIGEST"}
    ]
  }
}
```

Every registered task needs `id`, an actual `worktree`, `depends_on` and `prs`;
use an empty `prs` list before a PR opens. Missing global identity/dependency
fields make the whole audit incomplete. Missing task-specific cleanup fields
keep that task unknown. The collector also fails the whole run as incomplete on
malformed registration or incomplete API evidence; it never reports that as a
successful empty collection. Keep every planned slice in the dependency ledger. Archive manifest
files must be ordinary nonempty records as required by the guard. Include design,
screenshots and test evidence when present, not just this minimal example.
The guard verifies listed files and its minimum record set; it cannot infer
which required evidence was never created or omitted from the manifest. Compare
the manifest with the approved task's verification plan before considering
cleanup. Keep unknown preservation incomplete. The audit's verdict is not a
claim that every product requirement or artifact has been verified.
The self-contained Git bundle must retain the exact recorded head and pass a
temporary restore/fsck. A hash or bundle header alone is insufficient.
Differing cherry-picked heads need a separate mapping design; this guard does
not guess equivalence.

### Activity evidence

Use a fresh read-only app inventory and retain its original output. Derived JSON:

```json
{"source":"codex-app","captured_at":"UTC_TIMESTAMP","complete":true,
 "threads":[{"id":"ACTUAL_THREAD_ID","worktree":"ABSOLUTE_CHECKOUT","status":"idle"}]}
```

Only set `complete: true` when coverage is actually complete, including other
users of the checkout. Missing/paginated/ambiguous activity is unknown. All
registered threads must appear. Evidence must be no more than five minutes old;
running, waiting or planning tasks block. The script checks this supplied
evidence but cannot discover every app/CLI process itself. Revalidation and an
execution design are still needed before destructive cleanup can be enabled.
