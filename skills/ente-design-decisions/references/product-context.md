# Ente

Open-source, end-to-end encrypted photo storage. Flutter on mobile, plus web and
desktop clients, a Go server, and a CLI.

## Vocabulary — these two are not the same thing

The product uses "location" for two different concepts. Getting them confused
has already cost a multi-week redesign, so be precise in code, copy and commits:

- **Location** — a single photo's coordinates. A point. Editing it changes that
  photo's own metadata (stored in Ente, not written back to the file).
- **Place** — a saved, named circle on the map. The code calls it a *location
  tag*. Membership is **purely geometric**: a photo belongs to a place if its
  coordinates fall inside the circle.

Consequences that surprise people: creating a place changes no photo's metadata,
and the only way to move a photo into a place is to change the photo's own
coordinates. A photo cannot be "assigned" to a place.

Radius range is 1–1200 km, default 40 (`mobile/apps/photos/lib/core/constants.dart`).

## Design system

**Mobile:** `mobile/packages/ente_components/lib/components/` is the target
system — buttons, text inputs, bottom sheets, menus, app bars, banners, toasts,
chips, sliders, steppers, avatars. Icons in `mobile/packages/ente_icons`.

**Web:** `web/packages/base`, plus `gallery`, `media`, `accounts`.

Some screens still use the older widgets. `ente_components` is where things are
heading — but match the screen you are in rather than half-migrating one as a
side effect of unrelated work.

## Design and UX requests — read this before answering one

This applies to **any** request to change how something looks or works — a small
one ("what should this empty state say") and a large one ("this screen is
outdated, solve for it") alike. Size is not the test.

**Step one, always: read `.claude/design-in-flight.md`.** It lists areas
currently being designed, by file path. If what you are about to touch is
listed, **stop and report the entry** — do not propose a redesign, do not
recommend a direction. Work in a live area gets discarded or collides with
design that already exists outside this repo, and the code gives you no warning.

**Step two: load the design-decisions skill** in `.claude/skills/`. It covers
what you can settle yourself, what has to go to the designer, and how to find
what the product already does instead of inventing something.

Two things to do before answering any of those yourself:

1. **Read `.claude/design-in-flight.md`.** It lists areas currently being
   designed, by file path. If you are about to touch one, the entry says what is
   still safe to change and what to leave alone. Design work does not live in
   this repo, so the code gives you no warning on its own.
2. **Find what the product already does** in the same situation, and follow it.
   If nothing comparable exists anywhere, that is a new pattern — flag it for
   the designer rather than inventing one.

Decisions closed this way get one line in `.claude/design-log.md`.

## Figma

The Figma file belongs to the designer. Read it for reference if useful; do not
write to it. Concurrent writes have produced duplicate work that had to be
deleted by hand.
