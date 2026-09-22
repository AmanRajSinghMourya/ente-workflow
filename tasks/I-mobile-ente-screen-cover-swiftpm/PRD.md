# SwiftPM: ente_screen_cover

**Deferred — cancelled by Aman on 22 September 2026.** Local task work is abandoned under the one-time cleanup request. The existing chat is archived; no restart or publication is authorized. Plans, reviews and historical evidence below are retained. Recovery: `/Users/aman/Documents/Codex/ente-local-task-recovery-20260922T075859Z`.

Queue: Q002. [Task](codex://threads/01a0c739-e967-7e10-b51f-441b1226063f).
Host: local. Project: local-a0f48e7f2a6d317290c1ab9e6791ed49.
Assigned primary checkout: `/Users/aman/Development/ente-2` (read-only; preserve branch/dirt).
Implementation worktree: `/Users/aman/Development/ente-2/.worktrees/I-mobile-ente-screen-cover-swiftpm`.
Branch: `aman/mobile-ente-screen-cover-swiftpm`.

## Authorization

The opening task relays Aman's 22 September authorization from
[source workflow](codex://threads/01a0b92d-15fb-76a3-a3f1-194acf660e22), through
[mini coordinator](codex://threads/01a0c6ea-8e55-7c00-8798-52d124669141).
Routine technical planning, behavior-preserving implementation, commits and ready
PRs to AmanRajSinghMourya/ente:main are preauthorized for this five-package batch.
This supersedes historical Wednesday/calibration holds in Q002's queue context.
Product/behavior/security/data/supported-OS/maintenance decisions still need Aman.
No PR without verified native behavior. See [pilot PRD](../I-locker-swiftpm-pilot/PRD.md).

## Outcome and preserved behavior

Make the existing local ente_screen_cover plugin discoverable and linkable through
Flutter SwiftPM while retaining CocoaPods. Consumers are Photos, Auth and Locker,
through ente_lock_screen. Keep Dart APIs, method channel, Android implementation,
enable/disable idempotence, notification subscriptions and blur lifecycle identical.
Keep plugin iOS 13.0, Photos/Locker iOS 15.1 and Auth iOS 15.0 floors.
Do not change global/app SwiftPM or UIScene guards, app-lock settings or notifications.

## Source-grounded plan

Current plugin has one Swift file in ios/Classes and a podspec glob Classes/**/*.
No manifest or package test exists. Flutter 3.47.2 local plugins.dart locates
`ios/ente_screen_cover/Package.swift`; its current template declares a local
FlutterFramework dependency. The official plugin-author guide agrees.
The plugin observes didEnterBackground/didBecomeActive and finds the key window
through connectedScenes. All three consumers register GeneratedPluginRegistrant
and keep UIScene migration disabled. The native harness must retain that lifecycle.

One slice, estimated 100-200 changed lines including source relocation:
1. Relocate the byte-identical Swift source to
   ios/ente_screen_cover/Sources/ente_screen_cover/EnteScreenCoverPlugin.swift.
2. Add Swift tools 5.9 manifest, iOS 13, package/target ente_screen_cover, product
   ente-screen-cover, FlutterFramework local dependency/product as SDK template.
3. Update podspec source_files to that single shared source tree. No new dependency
   version, native code behavior change, resource or privacy-manifest invention.
4. Refresh consuming Podfile.lock podspec checksums only if deployment checks require
   it; no dependency-version churn. Record all app deployment floors unchanged.

## Acceptance and evidence before publication

A1. Before implementation, record missing expected manifest and source/API hashes.
After implementation, validate manifest name/product/platform/dependencies and
source identity; one source is selected by both package systems.
A2. Build a minimal external Flutter iOS harness using the real package through
SwiftPM; inspect generated package graph, registrant and build logs to exclude
CocoaPods fallback for this plugin. Exercise real channel enable/disable.
A3. Baseline CocoaPods and migrated SwiftPM: on a dedicated iOS Simulator, enable
cover, enter background/app switcher, confirm obscured contents, resume foreground
and confirm removed cover. Repeat enable/disable, disabled background, re-enable.
Preserve legacy app lifecycle (UIScene migration false); do not silently change it
to make a test pass. If baseline privacy behavior fails, investigate with Claude
and stop publication for a decision rather than change behavior under packaging.
A4. Retained CocoaPods harness builds/runs and podspec source identity check.
A5. Existing ente_lock_screen tests, format/analyze for affected Dart surface,
frozen pubspec check, enforced workspace resolution, and all three apps' pod
install --deployment from mobile-podfile-lock CI. Record generated-code or native
baseline blockers separately; never repair unrelated baseline issues.
A6. Diff stays within screen_cover plus necessary podspec-checksum lock entries;
all consuming app/pubspec/platform/lifecycle APIs unchanged.

## Review and publication

New persistent Claude design session, then implement/test; open ready fork PR
through authenticated gh with verified account/remote and Aman commit identity.
Proposed commit: Add SwiftPM support for screen cover.
Proposed title: [mobile] Add SwiftPM support for screen cover. Empty PR body.
Resume the exact Claude session for extensive code review after PR; inspect actual
Codex bot feedback. Record review SHA, links, findings/dispositions and refresh
checks/reviews after fixes. No /code-review. No force-push.

## References

- https://docs.flutter.dev/packages-and-plugins/swift-package-manager/for-plugin-authors
- Installed Flutter templates and lib/src/plugins.dart in /Users/aman/flutter.
