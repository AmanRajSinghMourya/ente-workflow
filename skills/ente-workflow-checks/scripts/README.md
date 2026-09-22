# Workflow checks

Local checks for task scope, PR setup, and test results that must still match the code.
They use Python 3.9+ and Git; the live PR check also uses authenticated `gh`.
They do not modify Git state or publish a PR. `run` executes the validation command you supply.

From any directory, test this one personal installation with:

```sh
python3 -B -m unittest discover -s ~/.codex/skills/ente-workflow-checks/scripts -p 'replay_*.py'
```

The tests use disposable repositories and simulated GitHub responses. They test
these tools, not Ente product behavior. CI does not currently invoke these scripts.

## Check an investigation stayed read-only

Save the starting state before investigating, then compare it afterward:

```sh
python3 -B ~/.codex/skills/ente-workflow-checks/scripts/checks.py snapshot --repo /absolute/checkout --snapshot /tmp/task-before.json
python3 -B ~/.codex/skills/ente-workflow-checks/scripts/checks.py unchanged --repo /absolute/checkout --snapshot /tmp/task-before.json
```

Use a fresh path outside the checkout for each task. Existing dirty work is allowed;
this detects changes to the starting state. It cannot attribute changes made by
another person or task in the same checkout, or prevent a write that is later undone.

## Check file scope or approved content

Write expectations from the agreed task before editing, then run:

```sh
python3 -B ~/.codex/skills/ente-workflow-checks/scripts/check_file_contract.py --repo /absolute/checkout --contract /tmp/task-files.json
```

The JSON supports `repo` (exact resolved checkout path), `branch`, `head` (full SHA),
`base` (full SHA), `allowed_paths` (repository-relative paths/globs), `must_change`,
and `files`. File assertions take this form:

```json
{
  "repo": "/absolute/checkout",
  "files": [
    {"path": "reference.md", "sha256": "REPLACE_WITH_FROZEN_FILE_HASH"},
    {"path": "labels.json", "json_values": {"title": "Approved title"}}
  ]
}
```

`allowed_paths` requires `base`; `must_change` requires both. A file can instead
use `text` for exact full contents, or `absent: true` for intentional absence.
These are file comparisons, not proof of correct UI or product behavior.

## Keep validation tied to the code

Run the relevant existing test/lint command through `run`, then use `verify`
before relying on that result. Keep its JSON and adjacent log outside the checkout:

```sh
python3 -B ~/.codex/skills/ente-workflow-checks/scripts/checks.py run --repo /absolute/checkout --cwd server --receipt /tmp/task-test.json -- ./scripts/test-with-postgres.sh host
python3 -B ~/.codex/skills/ente-workflow-checks/scripts/checks.py verify --repo /absolute/checkout --receipt /tmp/task-test.json
```

A failed command, changed source/staging/HEAD, or altered log invalidates the result.
Environment and device state are not recorded; choosing the right test remains necessary.

## Check a pushed PR candidate

Copy `example-contract.json` outside the checkout and replace its values with the
current task's authorized repository, account, branch, paths, and intended commits.
The example is a schema example, not a publishing policy.

```sh
python3 -B ~/.codex/skills/ente-workflow-checks/scripts/checks.py pr --repo /absolute/checkout --contract /tmp/task-pr.json
```

This reads live GitHub state through `gh`. `--offline` is diagnostic and cannot
return a full pass. `expected_commits` requires the exact intended commit set;
without it, a pass does not rule out an extra commit touching allowed files.
For a fork whose base must equal upstream, set `match_upstream: true` and
`upstream_repo`. An optional `pr_number` is the PR number to verify in `target_repo`.

## Check which API a test contacted

```sh
python3 -B ~/.codex/skills/ente-workflow-checks/scripts/check_api_origin.py --har /tmp/task-network.har --expected-origin http://localhost:8080 --api-path-prefix /public-collection/
```

This checks matching requests in the supplied capture; it does not capture traffic
or establish freshness. No matching requests is incomplete, not success.

The checks above return **0 for pass, 1 for fail, 2 for incomplete/error**. A failed or
incomplete result cannot support the action being checked. Do not change agreed
expectations merely to make a check pass.

## Check the PRD and actual change size

Make `<worktree>/.task` a directory symlink to its durable task folder in
`/Users/amanraj/development/ente-workflow/tasks/`. PRD, board, reviews and evidence
then remain outside the checkout while visible beside the diff. Before
implementation and again before review, check the PRD's UTF-8 byte count (maximum 50,000):

```sh
python3 -B ~/.codex/skills/ente-workflow-checks/scripts/check_task.py prd --prd /absolute/checkout/.task/PRD.md
```

Save the reported SHA-256 with the review inputs. To check that reviewers and the
approval proposal still refer to that document, run the same command with
`--sha256 <recorded-digest>`. This checks bytes and freshness, not the PRD's quality
or completeness. Extra explanations belong in chat; essential decisions do not.

Record the full base commit SHA for each planned PR, then measure its final
working-tree changes, including nonignored untracked files:

```sh
python3 -B ~/.codex/skills/ente-workflow-checks/scripts/check_task.py diff --repo /absolute/checkout --base <full-base-commit-sha>
```

The count is additions plus deletions: at most 500 passes, 501–1,000 warns, and
over 1,000 fails. Tests/generated text count; renames count as removal plus
addition. Binary changes are reported separately and make a complete line-count
decision unavailable. A file changed in both the index and working tree makes the
result incomplete: choose the intended version without silently changing Aman's
staging. Hidden Git flags or dirty submodules are also incomplete.

Plan by behavior and dependencies before coding; exact future diff sizes are
estimates. A failure means split/re-plan, or obtain an explicit task-specific
exception from Aman. These scripts do not intercept edits or authenticate approval.

## Scheduled review collection and cleanup audit

Read [automation tools](../references/automation-tools.md) for commands, the
task ledger, activity evidence and result meanings. `pr_reviews.py` collects
read-only GitHub evidence; `cleanup_guard.py` only audits eligibility. Honor the
hold in the shared control file. Neither tool publishes or deletes anything.
