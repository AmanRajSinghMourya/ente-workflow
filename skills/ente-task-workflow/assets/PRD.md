# Task: <name>

Status/outcome: <short current summary>

Intended behavior: <what should happen for the user>

Decision needed: <the remaining choice, or none>

Next step: <the concrete next action>

Chat: <verified task link; explicitly pending if no chat exists yet>

PR: <verified link when present; otherwise omit>

<!-- This is the single optional task-reading page. The agent fills it from a
one-line chat request, code investigation and answers to real gaps; Aman does
not fill this template. Keep routing, sessions, approval provenance and detailed
logs in supporting records. Explain the outcome/decision in chat as well. -->

## Outcome and scope
What should the user be able to do? What is explicitly outside this task?

## Current behavior and code
Relevant paths, existing pattern to reuse, and evidence of the bug or gap.

## Decisions
Accepted product choices; behavior/wording to preserve; unresolved choices that
block implementation. For a migration: compatibility, old data and rollout.
For competing designs: tradeoffs and the chosen approach, including Claude input
when useful. Keep longer explanations in chat.

## Acceptance examples and tests
Concrete input/action -> expected result, including failures and boundaries.
For a bug: exact reproducing test and its intended failure. For UI: what automated
tests cover and what still needs visual verification.

## Executable slices
For each slice: outcome, affected paths, test/check, dependency, estimated changed
lines and planned PR base. Estimates are not guarantees; measure the actual diff.

## Testing and review conclusions
Brief verified results, actionable review conclusions and material gaps. Keep
commands, transcripts and full reviewer findings in agent-maintained records.

## Follow-ups
Related old implementations that merit later work; remaining verification gaps.

<!-- Replace prompts with decisions. Keep this document <=50,000 UTF-8 bytes. -->
