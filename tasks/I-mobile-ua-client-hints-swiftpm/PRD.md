# SwiftPM: ua_client_hints

Queue Q006 · [Codex task](codex://threads/01a0c73b-4eeb-7c31-af6a-fe775f2970c3).
Host local; project local-ac1dc9d855099b51090b99fd92b5a561; assigned checkout `/Users/aman/Development/ente`.
Planned worktree `.worktrees/I-mobile-ua-client-hints-swiftpm`; branch `aman/mobile-ua-client-hints-swiftpm`.

## Authorization and outcome

The opening assignment relays Aman's 22 September batch authorization from [source workflow](codex://threads/01a0b92d-15fb-76a3-a3f1-194acf660e22): start Q006 now; routine technical planning, behavior-preserving changes, commits and ready PRs to AmanRajSinghMourya/ente main are authorized. Older Wednesday/calibration holds are superseded for this row. Product, behavior, security/data, supported-OS and maintained-fork decisions still need Aman. See [pilot](../I-locker-swiftpm-pilot/PRD.md).

Adopt the minimum sufficient released ua_client_hints SwiftPM package, retaining generated user agents and CocoaPods support for Photos, Auth and Locker. No complete app SwiftPM migration is claimed.

## Source evidence and plan

At implementation base719fbdd58d6e288ee6b52147898358eef10656d3 (fresh upstream main; rechecked after design review), Photos and ente_network pin 1.4.1. Photos calls userAgent directly; Auth/Locker consume ente_network, which calls userAgent on mobile. All share mobile/pubspec.lock and have iOS Podfile locks. Floors: Photos/Locker15.1, Auth15.0. Global and app SwiftPM/UIScene guards are false.

Downloaded archives were checked against pub.dev hashes and live 1.5.0 metadata on22September. All lib/ and android/src files, moved iOS Swift source and privacy content are byte-identical. Android build.gradle only changes package version, with toolchain unchanged.1.5.0 adds ios/ua_client_hints/Package.swift (Swift5.9, iOS12, ua-client-hints product, declared privacy resource); podspec paths move and floor10→12. Live pub/GitHub advisory queries returned empty lists. Evidence is in evidence/package-1.4.1, evidence/package-1.5.0, and advisory JSON.

1. Freeze focused method-channel output assertions and a native harness before dependency changes. Compare1.4.1 CocoaPods baseline with1.5.0 CocoaPods and SwiftPM on the same simulator and app metadata.
2. Review this plan in a new persistent Claude session. After technical review, fetch latest main and create the assigned worktree; reconfirm consumers/floors.
3. Change only the two pins to exact1.5.0 and regenerate the shared lock and three affected Podfile locks. Expected six files, under100 changed lines. Inspect for unrelated resolution churn; preserve all unrelated locks and guards.
4. Run focused contract tests, source/resource assertions, frozen resolution, CocoaPods deployment checks for all three consumers and applicable mobile CI equivalents. Native harness must prove plugin SwiftPM membership, generated registration, executable userAgent/client-hint behavior and included privacy resource. Test iOS device compilation without signing if available.
5. Publish only if native acceptance succeeds; then explicitly resume the same Claude session for extensive code review and inspect actual Codex bot feedback. Keep reviewed SHA and findings/dispositions in BOARD.

## Acceptance

All SwiftPM/native package assertions below apply to the scratch harnesses outside Ente. Repository CI checks cover dependency consistency and Dart checks; local build/run evidence separately covers native claims. CocoaPods and SwiftPM use distinct resource-bundle paths, each matched to its package privacy content.

- Same fixed getInfo map yields exactly the baseline userAgent, UserAgentData and all client-hint headers; native baseline and candidate on the same device/app metadata match.
- SwiftPM build contains ua-client-hints product, no ua_client_hints CocoaPod supplying it, generated registration and successful real getInfo calls. Bundle contains the matching PrivacyInfo.xcprivacy.
- CocoaPods candidate also builds/runs, includes privacy resource and retains outputs. All three app dependency graphs resolve exact1.5.0 and retain existing iOS floors.
- No Dart/API/Android behavioral changes; no overrides/forks; no pub cache edits; no SwiftPM/UIScene app guard changes.
- Frozen pubspecs, enforced lock resolution, formatting/static analysis, affected tests and Podfile deployment checks run with receipts. Baseline blockers remain explicit and never count as passes.

## Risks and exclusions

1.5.0's manifest predates explicit FlutterFramework dependencies in current guidance. Actual Flutter3.47.2 native compilation determines compatibility; a manifest alone is insufficient. If native linking fails, investigate with the same Claude session; do not silently upgrade to1.6/1.7 or maintain a fork.
No unrelated dependency upgrades, app source refactors, SDK installation/update, global settings changes or simulator sharing conflicts. Claim simulator ownership in the pilot BOARD before runtime testing. Source archive unpacking is under task evidence, never pub cache.
