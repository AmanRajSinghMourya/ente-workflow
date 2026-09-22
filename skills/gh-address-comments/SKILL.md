---
name: gh-address-comments
description: Help address review/issue comments on the open GitHub PR for the current branch using gh CLI; verify gh auth first and prompt the user to authenticate if not logged in.
metadata:
  short-description: Address comments in a GitHub PR review
---

# PR Comment Handler

Guide to find the open PR for the current branch and address its comments with `gh` when available.

## 0) Preflight
- Run `command -v gh`.
- Run `gh auth status`.
- If `gh` is missing or auth fails, ask the user to run `gh auth login` and continue with whichever fallback below is possible.

## 1) Inspect comments needing attention
- Preferred: run `scripts/fetch_comments.py` to print review threads and issue comments on the PR.
- Fallback when `gh` cannot be used: ask the user to paste the unresolved PR comments (or a PR link plus comment excerpts), then continue from that input.

## 2) Ask the user for clarification
- Number all review threads/comments and summarize the code change needed for each.
- Ask which numbered items should be addressed now.

## 3) Apply selected fixes
- Implement fixes for the selected comment numbers.
- If comments are unclear, state assumptions explicitly before editing.

## 4) Verify and report
- Run the smallest relevant checks for changed files.
- Summarize which comment numbers were addressed and what remains.

Notes:
- Do not rely on sandbox escalation parameters in this skill; follow the run-level sandbox/approval policy.
- If API/rate/auth errors happen mid-run, report exactly what failed and continue with pasted-comment fallback when possible.
