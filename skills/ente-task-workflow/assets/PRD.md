# Task: <name>

Codex chat: <verified task link; leave explicitly pending if no Codex chat exists yet>

<!-- Agent-maintained plan; explain the outcome/decision in chat as well.
Keep routing, session settings and approval provenance in BOARD's internal
section. Link useful supporting evidence instead of copying logs here. -->

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

## Follow-ups
Related old implementations that merit later work; remaining verification gaps.

<!-- Replace prompts with decisions. Keep this document <=50,000 UTF-8 bytes. -->
