---
name: recent-code-bugfix
description: Find and fix a bug introduced by the current author within the last week in the Ente monorepo (`/Users/amanraj/development/ente`). Use when a user asks for a proactive bugfix from their recent Ente changes, when the prompt is empty, or when asked to triage/fix regressions caused by their recent commits. Ensure the root cause maps directly to the author's own edits and validate with the smallest targeted check for the touched area.
---

# Recent Code Bugfix (Ente)

## Overview

Find one concrete bug introduced by the current author in the last week, implement a minimal fix, and verify it with the smallest relevant check. Operate in the Ente monorepo and only qualify issues whose root cause is directly tied to the author's recent edits.

## Repo Scope

Treat the current repository as a multi-stack monorepo. Prioritize fixes inside the area touched by the recent commits.

- `mobile/`: Flutter/Dart apps and packages (Photos, Auth, Locker, shared packages)
- `web/`: Yarn workspace for web apps and packages
- `desktop/`: Electron/TypeScript app
- `server/` and `cli/`: Go services and tooling
- `rust/`: Rust crates and bindings
- `infra/`: Workers and infra tooling

## Workflow

### 1) Establish recent-change scope

Identify author commits from the last week and extract candidate files.

- Determine author using `git config user.email` (fallback: `git config user.name`).
- List recent commits and changed files with `git log --since=1.week --author=<author> --name-only`.
- Build a de-duplicated candidate list and focus on source files first (not generated artifacts).
- If the prompt is empty, proceed with this default scope.

### 2) Find a concrete failure tied to those changes

Look for a reproducible failure in the touched area before editing.

- Prefer existing evidence first: local failing tests, lint output, runtime logs, or CI artifacts if present.
- If no failure is provided, run the smallest targeted check for the changed component:
- `mobile/`: targeted `flutter test <path>` or focused `dart analyze`/`flutter analyze` in the affected package/app.
- `web/` or `desktop/`: targeted lint/test command from the nearest `package.json` workspace/package.
- `server/` or `cli/`: targeted `go test` for the affected package.
- `rust/`: targeted `cargo test` for the affected crate.
- `infra/`: package-level lint/test in the affected worker/package.
- Confirm causality with git history (`git blame`, commit diff) and keep proof that the failing behavior comes from the author's recent commit(s).
- If failures are unrelated legacy issues, stop and report no qualifying bug.

### 3) Implement the minimal fix

Resolve only the identified regression.

- Edit only files required for the bugfix.
- Keep changes consistent with local conventions in that subproject.
- Avoid opportunistic refactors, broad cleanup, or unrelated hardening.

### 4) Verify

Re-run the same targeted check used to reproduce, plus any one adjacent check if needed.

- Prefer the smallest verification that proves the bug is fixed.
- Do not run whole-monorepo validation unless the fix scope requires it.
- If verification cannot run, state exactly what command was intended and why it was skipped.

### 5) Report

Summarize outcome with direct traceability to recent author changes.

- State the root cause and cite the author commit(s)/file(s) that introduced it.
- State the exact fix and why it is minimal.
- State verification command(s) and result(s).
- If no qualifying bug is found, explicitly say so.
