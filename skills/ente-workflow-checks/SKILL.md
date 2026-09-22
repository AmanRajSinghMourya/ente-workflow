---
name: ente-workflow-checks
description: Run Ente checks for investigation-only work, agreed file scope, validation tied to the latest code, PR preparation, local API request captures, bot review collection, or completed-task cleanup audits.
---

# Ente workflow checks

Use this skill's `scripts/` directory. Its canonical location is
`/Users/amanraj/development/ente-workflow/skills/ente-workflow-checks/scripts/`;
`~/.codex/skills/ente-workflow-checks` and `~/.claude/skills/ente-workflow-checks`
link to the same skill. Read `scripts/README.md` for commands. These are personal
tools, not Ente source, and have no publication/CI plan. Do not copy them into a
checkout or fall back to historical copies. Always pass the selected task's
actual checkout as `--repo`; the tool's own location is not the target repository.

Apply the checks relevant to the actual task:

- For PRD/implementation tasks, use `check_task.py prd` for the byte ceiling and
  expected document hash, and `check_task.py diff` for the actual change size.

- For investigation-only work, snapshot the starting state before investigating
  and compare it afterward. Preserve pre-existing changes.
- When file scope or exact wording is agreed, record those expectations before
  editing and verify them with `check_file_contract.py` afterward.
- For behavior changes, write a focused test and observe the intended failure
  before the fix when the behavior can be exercised reliably. Keep the agreed
  expectation fixed. Run broader existing CI checks after the code shape settles.
- Run the selected validation through `checks.py run`; use `verify` before
  claiming its result still applies. A green command is not proof of device or
  product behavior it did not exercise.
- For PR preparation, take the destination, account, scope, and authorization
  from current user/project instructions. Record intended commits explicitly.
  Run `checks.py pr` on the pushed candidate before relying on its readiness.
  Follow the existing permission requirement for live `gh` calls.
- If a local API test has a request capture, use `check_api_origin.py` to check
  the contacted server. Do not infer it from configuration alone.

For scheduled review collection or cleanup eligibility, read
[references/automation-tools.md](references/automation-tools.md). Honor the hold;
cleanup is read-only and an eligible result never authorizes deletion.

For the scope/validation checks, exit 0 passes; 1 fails; 2 is incomplete. Report the failed comparison or missing
evidence plainly. Do not broaden the expected scope to hide a failure. These
checks do not grant permission to stage, commit, push, or publish.
