# Locker Swift Package Manager pilot

Status: on 22 September Aman authorized starting the five easiest migrations
now on the Mac mini, split across `/Users/aman/Development/ente` and
`/Users/aman/Development/ente-2`. Its setup task below owns live selection,
queue assignments and execution evidence. This laptop copy is the planning
reference. Review-learning and cleanup schedules remain on their existing hold.
Source discussion: [Build Codex productivity workflow](codex://threads/01a0b92d-15fb-76a3-a3f1-194acf660e22).
Mac mini setup: [Set up Mac mini Ente workflow](codex://threads/01a0c6ea-8e55-7c00-8798-52d124669141).
Reference: [Flutter 3.47.2 upgrade, PR #12592](https://github.com/ente/ente/pull/12592).

## Outcome

Migrate the 11 plugins in Aman's warning, one independently scoped task per plugin.
Start with Locker; a shared dependency must still work in every consuming app.
This pilot is not a claim that all Photos/Auth dependencies have SwiftPM support.
After the plugin work, perform a separate Locker app/CI integration checkpoint.
Do not invent a PR for a package that already works or lacks a viable tested path.

## Aman's authorization for this batch

On 21 September Aman said: "yes open PR for what needed to be opened and wait for
one that needs my approval for product call". He then specified: "do a claude review
for the design and then OPEN pr then again claude review on same chat and also
codex review is enabled on the fork so there also one review is there".

For these migration tasks, this explicitly replaces the usual separate human
plan/code and commit/publication approvals for routine changes that preserve
behavior. Make a short source-grounded plan, obtain Claude's design review, resolve
technical findings, implement and validate, then open a ready-to-review PR on
**AmanRajSinghMourya/ente**, base main. Use the authenticated gh CLI, verify account
and push destination, use Aman's commit identity, keep structured commits and
apply the existing path-based PR title conventions. This is not approval to publish
to ente-io/ente or arbitrary third-party repositories. Keep the global instruction
files unchanged by this exception so other tasks retain their normal approvals.

After opening, ask Claude for a thorough code review in the **same Claude session
that reviewed this task's design**; do not use /code-review. Record the real session
ID in the task's BOARD, resume that ID explicitly, and preserve the review outputs.
Verify the host CLI supports session persistence; do not use --no-session-persistence,
an unrelated --continue session, or claim a fresh chat is the same session. Each
plugin task has its own Claude session. A Codex reviewer thread and the parent
should keep the task context in the same Codex task through subsequent fixes.

Inspect the enabled Codex review bot's actual feedback on the fork PR. Enabled is
not proof that review completed. Keep pending, failed and reviewed states distinct.
Resolve verified technical findings from both reviewers within scope, retain
rejected findings with reasons, rerun relevant checks after changes, and push
normally to the verified existing PR head. Never force-push. If code changes after
a review, record that the review applied to the older SHA and obtain the necessary
fresh review. Preserve comment URLs, hashes and dispositions in lasting notes.

Stop for Aman when a decision changes user-visible behavior, supported OS versions,
security/keychain/data semantics, or introduces a new maintained dependency fork or
replacement with an ongoing product/maintenance tradeoff. Use Claude to investigate
a hard technical blocker and present evidence/options. Being stuck does not authorize
publishing incomplete work, inventing a passing check, or dropping functionality.

## Verified starting evidence

PR #12592 merged on 7 September 2026 and deliberately deferred both SwiftPM and
UIScene migration. The current workspace and all three app pubspecs keep both
guards false. Existing release CI and the Podfile-lock workflow still use CocoaPods.
Keep those guard changes out of individual plugin PRs; UIScene remains out of scope.

Local repository/cache inspection on 21 September found exactly these 11 missing
Flutter-expected plugin manifests in Locker's cached graph. Auth and Photos have
additional plugins. This was a source/cache inventory, not a newly executed build
warning or validation on the Mac mini. Recheck the mini's current main and resolved
sources before deciding a package actually needs work.

Flutter's local detection looks for ios/<plugin>/Package.swift or the corresponding
darwin location. ente_mail's existing ios/Package.swift only tests MailCore and excludes
the Flutter plugin; open_file_ios has a manifest under Sources. Neither file by itself
proves working Flutter plugin integration. The installed-version evidence is below;
candidate newer versions must be checked live rather than assumed compatible.

## Task order and scope

### 1. ente_mail

- Current source: workspace: mobile/packages/mail. Consumers: Photos, Auth, Locker.
- Work: Add Flutter plugin SwiftPM packaging while preserving the existing MailCore native-test package.
- Evidence: Run the Dart mail contract tests and native MailCore tests; verify plugin registration and mail/attachment handoff in an iOS build.

### 2. ente_screen_cover

- Current source: workspace: mobile/packages/screen_cover. Consumers: Photos, Auth, Locker.
- Work: Package the existing native screen-cover plugin for SwiftPM without changing app-lock or privacy behavior.
- Evidence: Verify native background/app-switcher privacy coverage on iOS; widget tests alone do not prove it. Preserve current lifecycle wiring.

### 3. open_file_ios

- Current source: 1.0.4 via open_file 3.5.11. Consumers: Locker.
- Work: Check a compatible supported release and its parent dependency; current Package.swift is nested under Sources rather than Flutter's expected plugin directory.
- Evidence: Prove native registration/linking and a representative Locker file-opening handoff; mocked method-channel tests alone are insufficient.

### 4. file_saver

- Current source: 0.3.1; shared direct pins. Consumers: Photos, Auth, Locker.
- Work: Adopt compatible upstream SwiftPM support and update only the required shared pins/lock entries.
- Evidence: Verify iOS file export, filename/content, cancellation and shared consumers; retain other-platform behavior.

### 5. fluttertoast

- Current source: 8.2.14; shared direct pins. Consumers: Photos, Auth, Locker.
- Work: Adopt compatible SwiftPM support while preserving the native privacy resource and current toast behavior.
- Evidence: Verify native toast rendering and resource inclusion; check API changes in any proposed major release before upgrading.

### 6. ua_client_hints

- Current source: 1.4.1; Photos/shared network pins. Consumers: Photos, Auth, Locker.
- Work: Adopt compatible SwiftPM support, preserving the native privacy manifest and generated client headers.
- Evidence: Compare expected user-agent/client-hint output and privacy-resource inclusion in an iOS build.

### 7. cupertino_http

- Current source: 2.4.0 via native_dio_adapter 1.5.1. Consumers: Photos, Auth, Locker.
- Work: Resolve the native_dio_adapter constraint together with compatible upstream SwiftPM support; do not force an incompatible major through an override.
- Evidence: Verify native networking, cancellation and error handling through the actual adapter; check all shared consumers.

### 8. listen_sharing_intent

- Current source: 1.9.2; Locker direct. Consumers: Locker.
- Work: Migrate the plugin and validate the existing Share Extension import; determine whether upstream provides a compatible release.
- Evidence: Build the extension and verify cold/warm launch delivery, initial media, event delivery and reset behavior.

### 9. flutter_secure_storage

- Current source: 9.0.0; four deliberate pins. Consumers: Photos, Auth, Locker.
- Work: Investigate a packaging-preserving route. The repository warns that 9.2.4 leaves lock-screen keys after reinstall. Do not blindly upgrade or add a data migration.
- Evidence: Prove native existing-key preservation, read/write, upgrade/reinstall behavior and offline Auth data handling. Any security/data behavior change needs Aman.

### 10. ente_locker_frb

- Current source: 0.0.1 path: mobile/apps/locker/rust_builder. Consumers: Locker.
- Work: Design SwiftPM support for the Rust bridge, cargokit build, ONNX library location and static linker settings; it is not a manifest-only migration.
- Evidence: Verify target-device and supported simulator architectures, native bridge calls, ONNX resolution and symbol retention. Preserve existing deployment targets.

### 11. rive_native

- Current source: 0.0.16 pinned by rive 0.14.0-dev.13. Consumers: Photos, Locker.
- Work: Resolve the parent Rive pin and native package together; preserve native archives, setup scripts, frameworks and linker requirements.
- Evidence: Verify native setup/linking and representative Ente animations on the affected surfaces; run relevant existing native/event tests.

## Common acceptance checks

1. Preserve existing Dart/native APIs, resources/privacy manifests, app lifecycle,
   minimum OS support and non-iOS platforms. Keep CocoaPods compatibility during
   staged adoption as Flutter's plugin-author guide recommends.
2. Before changing a dependency, inspect the actual candidate release/source,
   compatibility constraints, changelog and pub/GitHub security advisories. A latest
   version number or Package.swift file is not sufficient. Do not edit pub cache.
3. Capture a baseline and focused tests/build checks before implementation. For
   actual bugs, reproduce the bug with a failing regression first. For packaging,
   prove the target plugin is built and registered through SwiftPM in a focused
   example/harness, not silently supplied by CocoaPods. Keep harness-only toggles
   out of unrelated committed app changes. Re-run the same checks after migration.
4. Run affected existing tests plus formatting, static analysis and relevant CI
   equivalents from .github/workflows. Verify frozen dependency resolution and
   retained CocoaPods compatibility where applicable. Dart tests alone do not
   prove native SwiftPM builds, resource inclusion or runtime handoffs.
5. Exercise the package-specific native behavior listed above. Record exact commands,
   device/simulator/platform and results. Missing native evidence is a blocker for
   claiming that behavior was verified. Record review/validation against the actual
   commit, keep the PRD under 50,000 UTF-8 bytes, and avoid unrelated lockfile churn.

All tasks share mobile/pubspec.lock and some shared manifests/Podfile locks. Give
each independent task an isolated I-<surface>-<package>-swiftpm worktree and matching
aman/<surface>-<package>-swiftpm branch after its technical plan and Claude design
review. This batch authorization supplies the routine implementation approval.
One writer per worktree. Keep dependency-resolution/integration changes coordinated;
do not let multiple agents edit a shared checkout. Rebase/merge work only in a way
consistent with existing PR history and Aman's no-force-push rule. Record dependent
PRs and don't claim an isolated PR is independent when it needs another's changes.

The initial one-task-first hold is superseded by Aman's 22 September request:
select the five easiest migrations, use GPT-6 Astra with extra-high reasoning and
Fast mode off, and start the mini TODO pickup now. Reuse the eleven existing rows
through queue.py; release only the selected five and leave six deferred. Alternate
their assignments between the mini's two repositories, preserving any already
running assignment. Record the actual host/path in each PRD, BOARD and opening
prompt. Routine plan/code/commit/PR-title/publication approvals are supplied for
solid technical fixes; genuine product/design/security decisions remain blocked
on Aman. Keep the Claude design review, same-session post-PR review, actual Codex
bot feedback and native validation requirements. Do not start cleanup or the
separate review-collection job early.
Use the shared task records and single .task directory symlink for each real task.

## Final Locker integration checkpoint

Only after the required plugins work, plan the Locker Xcode/CI SwiftPM transition
and verify the full app plus Share Extension, Debug/Release-relevant native linking,
and CocoaPods fallback/remaining dependencies as applicable. Inspect workspace
configuration precedence so enabling Locker does not accidentally migrate Photos
or Auth. Leave UIScene disabled. This is a separate dependent task, not included
in the initial 11-item import; split further only if the real diff requires it.
Do not announce complete SwiftPM migration while the workspace is still testing
only CocoaPods or any necessary plugin remains blocked.

## Sources to recheck

- Repository: mobile/pubspec.yaml; mobile/pubspec.lock; app pubspecs and iOS projects.
- Native packages: mobile/packages/mail and screen_cover; mobile/apps/locker/rust_builder.
- Secure-storage pins/comments: Photos/Auth pubspecs and packages/configuration and lock_screen.
- CI: .github/actions/setup-flutter/action.yml; workflows/mobile-lint.yml,
  mobile-podfile-lock.yml, locker-build.yml, photos-build.yml and auth-build.yml.
- [Flutter plugin-author guidance](https://docs.flutter.dev/packages-and-plugins/swift-package-manager/for-plugin-authors).
- [Flutter app integration guidance](https://docs.flutter.dev/packages-and-plugins/swift-package-manager/for-app-developers).
