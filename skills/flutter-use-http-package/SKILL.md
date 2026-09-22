---
name: flutter-use-http-package
description: Work on Dart/Flutter requests already implemented with package:http, or explicitly requested new http integrations. For Ente API work, reuse the affected service's existing network client and interceptors.
---

# Flutter networking

Trace the existing request and choose the client used by that service. Do not
replace an app's networking stack or add `http` simply to follow this skill.

For Ente, start from these paths relative to the selected checkout:
- Photos: `mobile/apps/photos/lib/core/network/network.dart`.
- Auth and Locker: `mobile/packages/network/lib/network.dart` and the calling
  service's existing `package:ente_network` client.

Preserve authentication, configured endpoints, interceptors, error handling and
client lifetime. Photos also uses `package:http` for error reporting; retain the
existing client there instead of imposing Dio on every request.

When working on an existing `http` request, use the API contract to determine
success codes and response parsing. Do not assume every successful response has a
JSON body or that only status 200 succeeds. Test the affected behavior with the
project's existing test utilities. Do not add networking or mocking dependencies
without checking the current project and the approved task scope.
