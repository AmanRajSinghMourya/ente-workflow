# <Plain-language task title>

<!-- Agent-written, not a form for Aman. Replace these prompts with a connected
account in newspaper order. Use the current facts and remove prompts/unused
links. The reader should understand the task without opening a link. -->

<Open with the problem or outcome and why it matters, in one or two sentences.
Make the current stage clear. Mention a critical gap or decision here if needed.>

[Chat](<verified task URL>) · [PR](<verified PR URL, when opened>)

<Explain what happens today with a concrete example. Introduce unfamiliar terms
before using them. State the established cause or what remains unknown.>

<Explain the proposed/completed change, how it addresses the problem and the
important reason for choosing it. Include material behavior to preserve or
tradeoffs. Do not describe planned work as completed.>

<Explain what the tests and reviews establish in terms of the behavior they
checked, their consequential findings and any remaining uncertainty. Before
implementation, explain how the agreed behavior will be verified instead.>

<State what happens next and any decision Aman needs to make. Give the context
and recommendation needed for that decision here. Do not end at "done" when
remote checks or another part of the task remains outstanding.>

<!-- Link completed reports here or alongside the review conclusion. Omit
unavailable links; never invent a Claude chat URL from a local session ID. -->
[Codex review](<report link>) · [Claude review](<report link>)

> [!info]- Implementation details
> Keep essential behavior, decisions and verification gaps in the article above.
> These details support implementation/review; they are not required reading.
>
> ## Scope and decisions
> Accepted behavior/wording, exclusions and unresolved choices. For migrations:
> compatibility, existing data, rollout, and whether existing patterns are sound.
> Record relevant alternatives and the source of accepted decisions. Preserve the
> full acceptance contract even when the readable explanation is short.
>
> ## Code and acceptance examples
> Relevant paths, existing patterns and evidence. For each meaningful input/action,
> state the expected result, failures/boundaries and focused test. For bugs, record
> the reproducing test and intended failure. For UI, distinguish automated coverage
> from visual/device verification. Link detailed evidence instead of pasting logs.
>
> ## Implementation slices
> Each slice's outcome, paths, check, dependency, estimated changed lines and PR
> base. Estimates are not guarantees; measure the actual diff. Omit when unnecessary.
>
> ## Supporting records and follow-ups
> Link full reviews, evidence and unqueued follow-ups when they exist. Keep exact
> routing, approval provenance and session-resume details in BOARD/internal notes.

<!-- Keep this document <=50,000 UTF-8 bytes, usually far below that ceiling.
Read the article without its links: can a new teammate follow the entire story? -->
