## Verdict

The **package delta is behavior‑preserving** and the **in‑repo change is CocoaPods‑only** — the 1.5.0 `Package.swift` is inert for all three Ente apps as long as the SwiftPM guard stays false. The missing `FlutterFramework` dependency is **not a blocker** for this task per the installed 3.47.2 sources. The main problems are in the *validation plan*, not the change: the SwiftPM acceptance criteria are unsatisfiable under the same section's own constraints, CI cannot cover any of the native claims, and the baseline SHA is stale.

## What I verified directly (read-only, from the evidence trees)

Byte‑equal 1.4.1 → 1.5.0 (I read both copies of each):
- `lib/ua_client_hints.dart`, `lib/src/ua_client_hints.dart`, `lib/src/user_agent_data.dart`, `lib/src/package_data.dart` — identical, including the UA format string and all eight `Sec-CH-UA-*` header keys.
- `android/src/main/kotlin/.../UAClientHintsPlugin.kt`, `AndroidManifest.xml`, `settings.gradle`, `gradle.properties` — identical; `android/build.gradle` differs only at `version '1.4.1'` → `'1.5.0'` (AGP 8.3.2, Kotlin 2.0.21, compileSdk 34, minSdk 22, JVM 17 unchanged).
- iOS plugin source: `ios/Classes/UAClientHintsPlugin.swift` → `ios/ua_client_hints/Sources/ua_client_hints/UAClientHintsPlugin.swift` — identical (moved only).
- `PrivacyInfo.xcprivacy` — identical content, moved into the target dir.

Podspec delta (`ios/ua_client_hints.podspec`): `source_files` `Classes/**/*` → `ua_client_hints/Sources/ua_client_hints/**/*.swift`; `resource_bundles` path updated (bundle **name `ua_client_hints_privacy` unchanged**); `s.platform` 10.0 → 12.0; license gains `:type => 'MIT'`; description reworded. Pod name, module name, and `s.dependency 'Flutter'` unchanged → CocoaPods module/registration surface is unchanged. `Package.swift` is not matched by `source_files`, so it won't be dragged into the pod compile.

Consumer reality in `/Users/aman/Development/ente`:
- Pins: `mobile/apps/photos/pubspec.yaml:196` and `mobile/packages/network/pubspec.yaml:20` (`1.4.1`); lock at `mobile/pubspec.lock:2749-2756`.
- Podfile.locks carry `ua_client_hints (1.4.1)` + checksum `92fe0d13…` in photos (`:232,514`), auth (`:122,261`), locker (`:117,248`); all three are `COCOAPODS: 1.17.0`. `mobile/apps/auth/macos/Podfile.lock` has no entry and must stay untouched.
- Floors: photos `15.1`, locker `15.1`, auth `15.0`. The podspec's 12.0 bump is fully masked: photos/auth `post_install` **delete** `IPHONEOS_DEPLOYMENT_TARGET`, locker **forces** `15.1`.
- Actual API usage is only `userAgent()` — `mobile/apps/photos/lib/core/network/network.dart:33` and `mobile/packages/network/lib/network.dart:23` (mobile‑gated). `userAgentData()` / `userAgentClientHintsHeader()` are unused in-tree.
- SwiftPM guard is per-project in `flutter: config:` at `mobile/pubspec.yaml:12`, `apps/photos/pubspec.yaml:286`, `apps/auth/pubspec.yaml:152`, `apps/locker/pubspec.yaml:111`.

## The FlutterFramework question, against /Users/aman/flutter (3.47.2 per `.github/actions/setup-flutter/action.yml:19`)

The PRD's framing is right but pessimistic. From the installed SDK:

- The current **template** does declare it (`templates/plugin_swift_package_manager/ios.tmpl/projectName.tmpl/Package.swift.tmpl:14-22`), and the SDK's own `packages/integration_test/ios/integration_test/Package.swift:14-22` does too — so 1.5.0's manifest is "old style".
- **App builds neither inject nor require it.** `SwiftPackageManager._dependenciesForPlugins` (`lib/src/macos/swift_package_manager.dart:158-232`) only symlinks the plugin package and adds `.package(name: "ua_client_hints", path: …)` + `.product(name: "ua-client-hints", package: "ua_client_hints")` to `FlutterGeneratedPluginSwiftPackage`. The only manifest rewriting is for **plugin‑to‑plugin** path deps (`:285-333`). No FlutterFramework validation anywhere on this path.
- The **only** validation is a *warning*, and only when building a plugin's own example app: `validatePluginSupportsSwiftPackageManager` (`lib/src/macos/darwin_dependency_management.dart:461-493`), reached via `_validateExampleAppPluginSupportsSwiftPackageManager` → `_loadPluginFromExampleProject` (`:384-449`). A consumer app never triggers it.
- The SDK explicitly accommodates non‑adopters: `_injectFlutterDependencies` in `lib/src/commands/build_swift_package.dart:1076-1111` — *"adding the FlutterFramework dependency was a secondary requirement that some plugins may not have adopted yet"* — but that patching runs only in the `flutter build swift-package` (add‑to‑app) flow, not `flutter build ios`.
- Structural compatibility otherwise checks out: manifest at `ios/ua_client_hints/Package.swift`, package name == plugin name, product name `ua-client-hints` matches the tool's `name.replaceAll('_','-')` expectation (`swift_package_manager.dart:224-229`), iOS 12 ≤ app floors, and `updateMinimumDeployment` (`:464-489`) raises the generated package's platform to the project's target.

**Conclusion:** no tooling hard‑fail, and zero effect on shipped Ente builds while `enable-swift-package-manager: false` holds. The residual risk is purely compile‑time `import Flutter` resolution inside the plugin target, which comes from inherited Xcode framework search paths rather than the manifest. That is empirical — one harness build settles it. Keep the PRD's "don't silently bump to 1.6/1.7, don't fork" rule.

## Blockers

1. **Acceptance contradicts itself.** "SwiftPM build contains ua-client-hints product, no ua_client_hints CocoaPod supplying it, generated registration" cannot be produced for any Ente app without flipping the four `enable-swift-package-manager: false` guards and letting the migration write `FlutterGeneratedPluginSwiftPackage` into `Runner.xcodeproj/project.pbxproj` — both forbidden two bullets later. Gating is `usesSwiftPackageManager = featureFlags.isSwiftPackageManagerEnabled && compatibleWithSwiftPackageManager` (`xcode_project.dart:237`) consumed at `darwin_dependency_management.dart:57-75`. Fix: scope every SwiftPM acceptance bullet explicitly to a scratch harness app outside the repo. Note the feature is `enabledByDefault` on stable (`features.dart:233-240`), so the harness needs **no** `flutter config` change — the global setting stays untouched by construction.
2. **No CI can evidence the native claims.** The repo has exactly two mobile workflows: `mobile-lint.yml` (Linux; frozen‑pubspecs, format, analyze, tests) and `mobile-podfile-lock.yml` (`pod install --deployment` for photos/auth/locker — resolution only, compiles nothing). "Applicable mobile CI equivalents" therefore cannot cover linking, registration, privacy‑resource inclusion, or runtime output. State this and record local build/run artifacts as the substitute, rather than implying CI coverage.
3. **Baseline SHA is stale.** PRD cites `08d1056…`; `evidence/source-before.json` and the checkout are at `ef563ca919…`. Re-anchor the PRD/BOARD baseline before branching, otherwise the "reviewed SHA" bookkeeping in step 5 is wrong from the start.
4. **"Six files" is asserted, not checked.** `mobile/apps/photos/ios/Runner.xcodeproj/project.pbxproj:683,779` contains inline pod framework input/output path lists that `pod install` regenerates. Add an explicit "no unrelated churn" gate (`git status --porcelain` == exactly the 6 paths) and require inspection — never a silent commit — if pbxproj appears. Also regenerate with **CocoaPods 1.17.0** to match all three locks; a different local pod version rewrites the `COCOAPODS:` line as unrelated churn (CI's `macos-latest` pod version is unpinned — pre-existing, worth noting in the PR).
5. **Privacy-resource assertion will misfire across managers.** CocoaPods keeps `ua_client_hints.framework/ua_client_hints_privacy.bundle`. SwiftPM's `.process("PrivacyInfo.xcprivacy")` produces a differently named resource bundle (SwiftPM's `<package>_<target>` convention) in a different location. Assert "a `PrivacyInfo.xcprivacy` with matching content exists somewhere in the built `.app`", plus a manager‑specific path check — do not assert one fixed bundle name across both.

## Smallest resolving checks

1. **Static, zero-build (record only):** package dir `ios/ua_client_hints/Package.swift`, package name `ua_client_hints`, product `ua-client-hints`, iOS floor 12 ≤ 15.0 — all already satisfied by the evidence above.
2. **Harness build A — CocoaPods 1.4.1 baseline, first**, on the claimed simulator, with fixed `CFBundleDisplayName`/`CFBundleShortVersionString`/`CFBundleVersion`/bundle id. Capture `userAgent()`, `userAgentData()`, `userAgentClientHintsHeader()` verbatim.
3. **Harness build B — CocoaPods 1.5.0**, same harness/simulator/metadata: outputs must match A byte-for-byte; `ua_client_hints.framework/ua_client_hints_privacy.bundle/PrivacyInfo.xcprivacy` present.
4. **Harness build C — SwiftPM 1.5.0**, a *fresh* scratch app (not the toggled A/B copy — once migrated, `flutterPluginSwiftPackageInProjectSettings` stays true and the empty-package path at `darwin_dependency_management.dart:64-75` muddies the comparison). Assert: generated `ios/Flutter/ephemeral/Packages/FlutterGeneratedPluginSwiftPackage/Package.swift` contains `.package(name: "ua_client_hints"` and `.product(name: "ua-client-hints"`; `GeneratedPluginRegistrant` registers `UAClientHintsPlugin`; no `ua_client_hints` under `Pods/` and no `ua_client_hints.framework` in the bundle; a `PrivacyInfo.xcprivacy` exists in the built `.app`; the three outputs equal A. **This single build is the definitive FlutterFramework answer** — if it fails with "no such module 'Flutter'", that is the exact failure to bring back to this session.
5. **In-repo sequence:** edit the two pins in lockstep (they pin the same package; changing one alone fails resolution) → `flutter pub get` → `ruby mobile/checks/frozen-pubspecs/check.rb mobile` → `flutter pub get --enforce-lockfile` → `dart format --set-exit-if-changed` → `flutter analyze --no-pub` → affected package tests → `pod install` in each of the three `ios/` dirs → re-run `pod install --deployment` to mirror CI → `git status --porcelain` gate.
6. **One end-to-end repo build** (photos, CocoaPods, simulator) asserting the outgoing `User-Agent` equals the 1.4.1 baseline. This is the only check that proves shipped behavior; everything else is upstream of it.

## Assumptions

- The two `evidence/package-*` trees are faithful extractions of the pub.dev archives; I compared files *within* the evidence and did not fetch anything. `evidence/release-1.5.0.json` records `archive_sha256 de6a9a4d…` and `published 2026-04-13`, but the tarball hash check itself must be executed and receipted during implementation.
- `/Users/aman/flutter` is the 3.47.2 SDK CI uses (no `version` file present; inferred from the pinned action and source layout).
- Xcode ≥ 15 is installed (`compatibleWithSwiftPackageManager`, `xcode_project.dart:225-230`) and a simulator is claimed per the pilot BOARD before runtime work.
- No pub cache mutation; the harness lives outside `/Users/aman/Development/ente`.

## Recommendations (non-blocking)

- Say plainly in the PR body: the repo stays CocoaPods-only, and the only shipped effect is the podspec source path + floor change; SwiftPM support is latent until the guards are lifted. That keeps the PR honest and matches the PRD's "no complete app SwiftPM migration is claimed".
- Anchor the behavioral baseline on `userAgent()` (the only API in use) plus the request headers the two clients actually build, and state the broader `userAgentData()`/client-hint comparisons as superset evidence from the harness.
- Record the podspec floor analysis (10→12 masked by all three `post_install` blocks) in the PR body; it pre-empts the obvious reviewer question about the iOS 12 bump.
- Keep the PRD's escalation rule verbatim: if the SwiftPM harness fails to link, report back here — no fork, no silent 1.6/1.7 bump, no overrides.