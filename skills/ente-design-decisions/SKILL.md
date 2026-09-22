---
name: ente-design-decisions
description: Apply the Ente design team's current draft guidance to design, UI/UX, copy, component choices and Figma-linked tasks. Check in-flight design, find source precedents, and surface product/design choices before implementation approval.
---

# Ente design decisions

This adapts Aman's supplied `/Users/amanraj/Downloads/ente-design-kit/` for Codex.
It is a **draft team policy**, not proof that a design is correct or current.
Current user instructions and the approval gate in `ente-task-workflow` take
precedence. Do not install the kit's CLAUDE.md or AGENTS files into the repository.

Before proposing a UI/UX direction, read
[references/design-in-flight.md](references/design-in-flight.md), then
[references/team-skill.md](references/team-skill.md). Interpret its relative
`.claude/` references through this installed skill. Read
[references/product-context.md](references/product-context.md) for relevant
vocabulary. Verify code facts against the selected checkout rather than trusting
hard-coded counts, ranges, component names or the claim that no user research exists.

The supplied in-flight register is a snapshot imported on 2026-09-21; there is no
connected update pipeline here. Its listed restrictions are evidence of a possible
collision. An absent entry does not prove no designer is working on that area.
For a listed area, report the exact entry and distinguish allowed maintenance
from changes requiring a decision. “Parked” does not mean unrestricted.

Find the closest existing behavior on the same surface and cite its path. Match
the complete interaction, ownership/permissions and states, not just the component
name. Prefer shared components when appropriate; don't half-migrate a screen or
add general machinery as a side effect. Existing code is a precedent to evaluate,
not proof that the design should be copied unchanged.

For unresolved choices about new patterns, terminology, behavior, shared
components or design collisions, first use the Codex/Claude planning consultation
in [the task workflow](../ente-task-workflow/references/reviews.md#planning-opinion).
Give the independent reviewer the relevant team guidance and visual evidence.
Then tell Aman the recommendation, tradeoffs and any remaining disagreement. The kit's
“You're the approver” means the human developer, never the agent. Do not contact
the designer, post messages, or claim designer approval without Aman's instruction.
Safe bug fixes can be investigated; code still waits for Aman's approved plan.

For a Figma link, use the applicable Figma skill to read the relevant nodes and
states. The kit authorizes reference reading, not writing into the team's file.
Show any conflict between the Figma design, current code and accepted requirements
to Aman before selecting a direction. Follow an explicit user decision.

Record the agreed design and source precedent in the task PRD, then append a short
entry to `/Users/amanraj/development/ente-workflow/design-log.md` with
date, task, decision, source and actual approver. Mark unresolved choices as
pending; don't make a log entry into fabricated approval. This shared log is local;
it is not automatically visible to the design team.

Current gaps: register ownership/synchronization, links to authoritative Figma
nodes, accessibility/text-scale/localization requirements, responsive/platform
states, loading/error/empty cases, and screenshot/golden acceptance procedures.
Include the relevant gaps in a task's plan; do not claim the kit settles them.
