# Q003: open_file_ios SwiftPM readiness

**Deferred — cancelled by Aman on 22 September 2026.** Local task work is abandoned under the one-time cleanup request. The existing chat is archived; no restart or publication is authorized. Plans, reviews and historical evidence below are retained. Recovery: `/Users/aman/Documents/Codex/ente-local-task-recovery-20260922T075859Z`.

Chat: [Q003](codex://threads/01a0c73b-4733-76a3-a6c5-655aa04909d4).
Assignment: local; project local-ac1dc9d855099b51090b99fd92b5a561; primary checkout `/Users/aman/Development/ente`. Never edit or switch primary checkout.
Worktree after design review: `/Users/aman/Development/ente/.worktrees/I-mobile-open-file-ios-swiftpm`; branch `aman/mobile-open-file-ios-swiftpm`.

## Authorization and outcome

Aman's 22 September immediate five-package pilot authorization is relayed in this task's opening message from [coordinator](codex://threads/01a0c6ea-8e55-7c00-8798-52d124669141), based on [source](codex://threads/01a0b92d-15fb-76a3-a3f1-194acf660e22). It permits routine technical planning, behavior-preserving implementation, commits and ready fork PRs to AmanRajSinghMourya/ente:main. No repeated routine approval gate. Product, behavior, data/security, supported-OS and maintained-fork decisions still require Aman. See [pilot PRD](../I-locker-swiftpm-pilot/PRD.md). Sequence: Claude design review in a persistent session, implementation/verification, fork PR, extensive Claude code review resuming that exact session, and actual Codex bot feedback.

Outcome: move Locker's resolved open_file_ios to SwiftPM-ready 1.1.0 as a prerequisite for the separate app/CI integration checkpoint. Root and Locker SwiftPM/UIScene guards explicitly stay false; Locker continues using CocoaPods. The isolated harness proves package readiness, and Locker smoke verifies preserved behavior.

## Source-grounded plan

Initial source inspection at 08d10562021967292c7b106d369fcf41d0f30bce; fetched main after design review and created worktree at 719fbdd58d6e288ee6b52147898358eef10656d3. Relevant dependency/native paths are unchanged. Locker alone directly uses open_file 3.5.11; its ^1.0.4 platform constraint permits open_file_ios 1.1.0. Update the workspace lock resolution for open_file_ios from 1.0.4 to 1.1.0, including the solver-generated Dart SDK floor from >=3.11.0-0 to >=3.11.0. The selected Dart3.13.2 already satisfies this floor. Do not add a redundant direct platform dependency or upgrade parent to 4.0.0 (unrelated Android permission change).

Verified downloaded archives against pub.dev SHA256. Actual lib/open_file_ios.dart, Objective-C implementation and header are byte-identical. 1.1.0 moves Package.swift from ios/open_file_ios/Sources to ios/open_file_ios, changes manifest/source configuration and uses FlutterFramework. The podspec description changes; its source glob, native version 1.0.3 and iOS12 floor remain. SwiftPM requires iOS13 and tools5.9; Locker already targets iOS15.1. Flutter3.47.2/Dart3.13.2 satisfy candidate Flutter>=3.41/Dart^3.11. Live pub.dev and GitHub pub advisories are empty for open_file and open_file_ios; archive has no executable hooks.

One slice, estimated two files and <20 changed lines: mobile/pubspec.lock and mobile/apps/locker/ios/Podfile.lock (required podspec description checksum). Retain all other dependency versions. Do not change app code, global/app SwiftPM or UIScene guards, other platforms, minimum OS, native plugin cache, or lifecycle wiring. Keep harness and validation artifacts in this task's evidence folder, outside product diff.

## Acceptance and validation

1. Baseline archive lacks Flutter-expected ios/open_file_ios/Package.swift; candidate contains it. Resolve only open_file_ios, inspect diff, then flutter pub get --enforce-lockfile. Confirm parent and all other packages unchanged.
2. Use an isolated Flutter iOS harness with reviewed official open_file3.5.11 and open_file_ios1.1.0; SwiftPM on only in harness. Prove generated registration, SwiftPM target compilation/link symbols and absence of target CocoaPods fallback. Baseline1.0.4 captures failure/fallback for the same check. Use current Flutter tool source as integration reference.
3. On an owned iOS Simulator, exercise native missing-file result, valid named text/PDF preview and dismiss/result callback, then representative Locker file-opening handoff. Preserve Locker's current non-UIScene AppDelegate/Info.plist behavior when checking compatibility. A fake channel or harness-only modern lifecycle does not satisfy Locker runtime proof.
4. Run existing Locker file-util tests (filename/content handoff) and affected Locker suite; frozen pubspec checker, formatting, analysis, locked dependency resolution, and CocoaPods --deployment checks following mobile-lint/mobile-podfile-lock workflows. Account for generated Rust/localization prerequisites using CI commands. Record baseline/environment failures accurately; do not repair unrelated code. Device archive may be replaced by simulator build locally without claiming signing/TestFlight evidence.
5. Freeze final patch, PRD digest, base and check receipts; inspect diff; publish only if native acceptance holds and required checks are satisfied. Use gh verified account/aman-review destination and AmanRajSinghMourya <amanrajmourya7@gmail.com> identity. Proposed commit: Update Locker file opening plugin for SwiftPM readiness. Proposed ready PR title: [mob][locker] Update file opening plugin for SwiftPM. Empty body. Record actual publication SHA; extensive same-session Claude review and Codex bot feedback with findings/dispositions and freshness.

## Resolved validation questions

Native RootViewController uses connectedScenes on iOS13+ while Locker retains legacy AppDelegate and UIScene migration off. Both original-lifecycle baseline/candidate probes and the real Locker FileUtil.openFile cached-file handoff passed on the owned iPhone17/iOS26.5 simulator. No lifecycle change was required. The candidate generated SwiftPM graph resolves FlutterFramework, links OpenFilePlugin and has no CocoaPods fallback. Evidence is indexed in evidence/validation-summary.md. These results cover this simulator and cached-file path; no signed device archive or logged-in remote-download journey is claimed.
