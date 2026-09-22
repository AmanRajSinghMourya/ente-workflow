---
name: design-decisions
description: Use for ANY design or UX question while building this product — from small ones (what an empty state says, which component to use, how to order actions, what a label reads) to large ones phrased as "the UX here is bad", "this screen is outdated", "redesign this", "solve for it", or any request to improve how something looks or works. Checks whether the area is already being designed, finds what the product already does, and applies it. Escalates anything that would invent a new pattern or reopen live design work. Load this before answering any such request, however it is phrased.
---

# Small design decisions

For when you're building and there's no design for the thing in front of you.
You're the approver — this doesn't go to the designer unless it has to.

## First: is this area already being designed?

**Read `.claude/design-in-flight.md` before anything else.** It lists the areas
currently in design, by file path.

If what you're about to touch is listed there, stop and read the entry. Each one
says what's still safe to change and what to ask about. Work done in a live area
either gets discarded by the redesign or collides with it — and you have no way
to know from the code alone, because the design work doesn't live in this repo.

This is the check that catches the expensive mistake. The rest of this skill
catches the cheap ones.

## The one rule

**Cite the precedent, or escalate.**

If the product already solves this situation somewhere, find it, apply it, name
where it came from. If it doesn't, say so and stop — don't invent.

That sounds pedantic. It isn't. The danger isn't answering one question wrong,
it's that an invented pattern gets built, ships, and becomes the thing the next
question gets answered against. Ente's photo-selection bar has **fifteen
actions** in one scrolling row. Nobody added fifteen. Fifteen people each added
one reasonable button, locally, and every one of those was a small design
question correctly answered.

So: applying the design system is free. Extending it is a decision, and it isn't
yours or mine to make quietly.

## Where precedent lives

**Mobile (Flutter)** — `mobile/packages/ente_components/lib/components/`
51 files. Real components, use them by name rather than rebuilding:
`button`, `text_input_component`, `bottom_sheet_component`, `menu_component`,
`popup_menu_component`, `app_bar_component`, `banner_component`,
`toast_component`, `filter_chip_component`, `tag_chip_component`,
`slider_component`, `stepper_component`, `settings_item`, `divider_component`,
`avatar_component`, `selection_summary_chip_component`, `selection_controls`.

Icons: `mobile/packages/ente_icons`. Shared base: `mobile/packages/base`.

**Web** — `web/packages/base`, plus `gallery`, `media`, `accounts`.

**Some screens still use the old design system.** `ente_components` is the
target. If the screen you're in uses the old widgets, match the screen you're in
— don't half-migrate it as a side effect. Note it in the log instead.

**The strongest precedent is the same situation elsewhere in the product.** Before
reaching for a component, search for the nearest existing case: another empty
state in the same surface, another destructive confirm, another permission
prompt. Copy what's there.

## What closes here

- Which component to use
- Copy for an empty, error, loading or permission state
- Ordering and hierarchy of actions in a sheet, dialog or menu
- Where a control goes, when the surface already has a convention
- Icon choice, when one exists for the concept
- Spacing and layout that follows an existing screen
- A label, when the concept behind it is already settled

## What escalates to the designer

Stop and say so if the answer would:

- **Invent a pattern** — no precedent found anywhere in the product
- **Add or change a component** in `ente_components`, or add a variant or state
- **Introduce or rename a concept** — a new noun, a new permission, a new object
  state. Ente has already been bitten by this: "location" and "place" are two
  different things sharing one word, and it took a multi-week redesign to untangle.
- **Change what an existing action does**, even slightly
- **Cross surfaces** you don't own — a change whose consequence shows up in
  another feature's screens
- **Turn on taste** — visual style, brand, tone of voice
- **Trade one user group against another**

Size is not the test. A one-word label change that introduces a new concept
escalates; a whole empty-state screen that follows three existing ones does not.

## The log

Every decision closed here gets one line in `.claude/design-log.md`:

```
2026-09-21 | Empty state for shared-with-me | Used banner_component + copy pattern from albums empty state (mobile/.../albums_empty.dart) | @dev
```

What was asked · what was decided · **the precedent it rested on** · who approved.

The designer doesn't gate these. She reads the log. The point is that six
reasonable local answers can add up to a direction nobody chose — the log is how
that gets caught while it's still six and not fifteen.

Escalations go in too, marked `ESCALATED`, so it's visible what's waiting on her.

## Figma

**Don't write to it.** The Figma file is the designer's, and concurrent writes
have already produced duplicate sections she had to delete. Reading it for
reference is fine. Producing screens in it is not this skill's job.

## What I'll push back on

With the designer, I argue about framing and evidence. Here, I argue about
**implementation convenience deciding the design.**

If the reason for an answer is that it's cheaper to build, faster to ship, or
avoids touching a messy file — that's a real constraint and worth saying out
loud, but it's not a design rationale. I'll name it as the tradeoff it is rather
than dressing it up.

I'll also tell you when a small question is a symptom. "What should this fourth
confirm dialog say" is sometimes a copy question and sometimes evidence that the
flow has four confirms.

I won't pretend to know things I can't: no user research exists for this product,
so "users will prefer this" is never available. "This matches what the product
already does" is.
