---
name: flutter-setup-declarative-routing
description: Set up declarative routing when explicitly requested for a new Flutter app or an app already using go_router. For existing Ente navigation and deep-link fixes, follow the app's current routing path without introducing go_router.
---

# Flutter navigation

For an existing app, trace the current navigation and deep-link entrypoints first.
Use its existing route helpers and back-stack behavior. A deep-link bug is not
permission to replace its router.

In Ente, inspect the affected app and shared components. Useful starting points
relative to the selected Ente checkout are:
- Photos: `mobile/apps/photos/lib/services/app_navigation_service.dart`.
- Auth: `mobile/apps/auth/lib/utils/navigation_util.dart`.
- For other surfaces, follow the actual call site and its navigation helper.

Ente's current mobile apps do not use `go_router`. Do not add it for a routine
navigation fix. Propose a migration only when requested or supported by a separate
approved design. Preserve platform deep-link configuration unless it is involved
in the demonstrated failure.

For a new app or an approved declarative-routing migration, consult the chosen
router's current official documentation and package checks before adding it.
Derive tests from the required entry route, back behavior and invalid-link cases.
