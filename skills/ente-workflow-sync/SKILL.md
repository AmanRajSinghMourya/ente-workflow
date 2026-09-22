---
name: ente-workflow-sync
description: Distribute personal Ente skills and workflow instructions through the private Git repository when requested or after an approved skill change. Task lists and task records are local; continuous file sync is retired.
---

# Workflow distribution

The private `AmanRajSinghMourya/ente-workflow` repository shares skills and workflow
instructions. TODO, `.workflow/queues/`, `tasks/`, archives, app settings,
credentials and raw evidence stay on the originating host for now.

The old Python sync helper and LaunchAgent installer are retired. Do not recreate
continuous sync or schedule a replacement. Aman is preparing the agent-definition
distribution rules separately; wait for those details before changing registration.

For an approved workflow update, inspect Git status and the actual diff. Stage
only the named skill/instruction files. Preserve user-staged or unrelated changes;
never use `git add -A` across this folder. Workflow-repository commits/pushes are
preauthorized, but Ente product Git actions retain their separate approval gates.

Do not publish pending removal of historically tracked task records until the
other host has preserved its own task files and agreed to that transition. On
receipt of a workflow update, preserve local notes before applying it. Git can
remove formerly tracked files even when the new ignore rules exclude them.
Do not claim the other Mac has loaded an update without verifying it there.

Personal Codex/Claude skill directories link to this host's `skills/` directory.
Preserve unrelated skills and vendor-managed packs. Plugin activation and
credentials are host-local; copying files does not configure or authenticate them.
