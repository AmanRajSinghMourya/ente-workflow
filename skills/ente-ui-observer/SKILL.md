---
name: ente-ui-observer
description: Observe an Ente mobile verification flow from saved simulator screenshots and interaction evidence, recording adjacent bugs, UX questions and design mismatches for later triage. Use as a separate observer during an approved task; the parent remains the simulator controller.
---

# Ente UI observer

Help Aman discover problems while another task is being verified, without turning
that task into an unapproved redesign. This skill supplies instructions, not a
continuous screen stream or an automatic capture service.

## Handoff and ownership

The parent provides the approved PRD, the current flow and stopping point, the
unchanged/changed build identities, and paths to actual screenshots plus numbered
interaction notes. Include accessibility snapshots/logs when available and the
specific Figma nodes when supplied. The observer reads each captured batch and
writes only the assigned lasting task's `followups.md`. It owns those writes
during an active batch; the parent adds its own observations and triages only
after the observer returns.

One agent controls the simulator. The observer must not tap, navigate, boot/reset
devices, alter fixtures, change code, edit requirements or modify Figma. It has no
permission to start another task or expand the route being tested. If observation
needs another interaction, record a suggested reproduction for the parent to
consider at a natural checkpoint. Do not invoke active-voice-only screen tools
from a text task or invent a live feed.

The parent can send additional capture batches while the observer works. When no
batch remains, the observer returns its notes; the parent may resume it with the
next batch. Stop when the parent finishes this verification session. Keep routine
findings in the file and return a compact digest at the checkpoint/completion;
do not message the user or repeatedly interrupt the parent. Promptly flag an
observed risk of imminent data loss so the controller can stop the action.

## What to look for

Read `$ente-design-decisions` before making design comparisons. For linked Figma
nodes, use the applicable Figma skill for reference reading only. Current accepted
decisions take precedence over the draft kit; label conflicts instead of silently
choosing a new design. Do not invoke a whole-app audit for a bounded observation.

Inspect the supplied route for visible layout/copy problems, unclear actions,
inconsistent state/feedback, loading/error/empty states and accessibility clues.
Do not invent a quota of findings. Screenshots can show clipping; they cannot
prove persistence, permissions, screen-reader operation or the absence of races.
Label a confusing interaction as a UX question unless its expected behavior has
an accepted source. Preserve intermittent observations as needing reproduction.

Each finding needs a stable ID, category (observed bug, UX proposal, design
mismatch or refactor), build/run, device/state, actions, actual versus expected
result, the source of that expectation, evidence paths, reproduction status and
suggested next decision. Say whether it appeared on the before or after build;
absence from one screenshot does not prove it was introduced by the change.
Read existing findings and deduplicate by behavior rather than phrasing.

## Parent triage and the next task

The parent verifies the evidence and decides whether it is a current-task defect
or unrelated follow-up. Current regressions/unmet acceptance criteria go into the
current review, not a hidden backlog. The observer does not make final product,
design or code-review decisions.

At completion the parent shows a short list and offers to add selected findings
to `/Users/amanraj/development/ente-workflow/TODO.md`. Retain evidence
in `followups.md` even when Aman defers or declines the item. TODO means pending
investigation/design; it never means permission to create a worktree or implement.
No automatic issue filing, messages to designers or publication of screenshots.
