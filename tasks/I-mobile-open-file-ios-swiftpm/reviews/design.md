I have enough to give the review. Everything below is grounded in files I read; I ran nothing.

---

# Q003 — open_file_ios SwiftPM readiness: independent design review

## Verdict

The **dependency choice is correct and minimal**, and the **1.1.0 package itself is genuinely SwiftPM-ready in exactly the form Flutter 3.47 prescribes**. But the PRD rests on a load-bearing repo fact it never states, and as a result its **outcome statement overclaims** and two acceptance items are mis-scoped. No blocker to *doing* the change; there are blockers to the change *meaning what the PRD says it means*.

---

## F1 — Headline: SwiftPM is explicitly disabled for Locker, and the PRD never says so

`evidence/source-snapshot/mobile/apps/locker/pubspec.yaml:106-112`:

```yaml
flutter:
  # Temporary Flutter 3.47 rollout guards: preserve CocoaPods and existing
  # app lifecycle wiring. Remove after CI and Xcode support SwiftPM and each
  # app has deliberately migrated to UIScene.
  config:
    enable-swift-package-manager: false
    enable-uiscene-migration: false
```

Same block at `evidence/source-snapshot/mobile/pubspec.yaml:7-13`. Project-level `flutter: config:` overrides the global/default flag — `flutter_features_config.dart:43-62,104-115` resolves *project manifest → global config → env var*, and `flutter_features.dart:59` wires `isSwiftPackageManagerEnabled` to it. The feature is otherwise `enabledByDefault: true` on stable in 3.47 (`features.dart:233-240`), so this guard is doing real work.

Three consequences:

1. **The PRD's stated outcome — "make Locker's existing open_file implementation discoverable/buildable through Flutter SwiftPM" — is not achieved by this change.** With the guard set, `XcodeBasedProject.usesSwiftPackageManager` is false (`xcode_project.dart:237-238`), `swift_package_manager_enabled.ios` is written `false` into `.flutter-plugins-dependencies` (`flutter_plugins.dart:1315-1331`), and `podhelper.rb:327-330` therefore installs `open_file_ios` as a pod regardless of its `Package.swift`. The new manifest is **inert for Locker**. This is a *prerequisite* commit, not an enablement.

2. **The expected two-file diff is correct — precisely because of this guard.** Had SwiftPM been on, `podhelper.rb:330` (`next if swift_package_manager_enabled && swift_package_exists`) would have *removed* `open_file_ios` from `Podfile.lock` entirely, not changed a checksum. The PRD reaches the right answer without naming the mechanism, which is fragile: if someone lifts the guard in a parallel task, this plan's expected diff silently inverts.

3. I confirmed the guard is load-bearing empirically. `url_launcher_ios-6.4.1/ios/url_launcher_ios/Package.swift` exists in the pub cache and `url_launcher_ios` is still a pod in `mobile/apps/locker/ios/Podfile.lock:119,149`; same for `local_auth_darwin`, `sqflite_darwin`, `shared_preferences_foundation` (all have `darwin/<name>/Package.swift`). That combination is only possible with `swift_package_manager_enabled.ios == false`.

**Recommendation:** rewrite the outcome line to something like *"Move open_file_ios to the SwiftPM-ready 1.1.0 so that Locker stops being blocked on this plugin when the `enable-swift-package-manager` guard is eventually lifted; no change to how Locker builds today."* The proposed commit subject **"Enable SwiftPM support for Locker file opening" is inaccurate** and will not survive review — nothing is enabled. The PR title `[mob][locker] Update file opening plugin for SwiftPM` is acceptable; with an empty PR body the commit message carries the whole burden, so it must be precise.

---

## F2 — Narrow dependency choice: correct

- `open_file 3.5.11` declares `open_file_ios: ^1.0.4` (`~/.pub-cache/hosted/pub.dev/open_file-3.5.11/pubspec.yaml:17`) → 1.1.0 is admitted. ✔
- Locker declares `open_file: 3.5.11` (`source-snapshot/mobile/apps/locker/pubspec.yaml:85`); `open_file_ios` is transitive (`source-snapshot/mobile/pubspec.lock:1846-1853`, version `1.0.4`). ✔
- **The frozen-pubspec checker only validates declared deps**, walking `dependencies`/`dev_dependencies`/`dependency_overrides` of each workspace pubspec (`mobile/checks/frozen-pubspecs/check.rb:5,98-109`). A transitive lock bump is invisible to it; `open_file: 3.5.11` still matches its lock entry. ✔ This independently confirms "do not add a redundant direct platform dependency" — adding one would put a platform implementation package in Locker's pubspec and buy nothing.

---

## F3 — Baseline/candidate discovery claim: correct, and stronger than the PRD states

`Plugin.pluginSwiftPackageManifestPath` resolves to `<package>/ios/<plugin_name>/Package.swift` (`plugins.dart:458-477`); `supportSwiftPackageManagerForPlatform` gates on that file existing (`plugins.dart:479-485`). `podhelper.rb:329` checks the identical path.

- 1.0.4 ships it at `ios/open_file_ios/Sources/Package.swift` → not found. ✔
- 1.1.0 ships it at `ios/open_file_ios/Package.swift` → found. ✔

Worth adding to the PRD: 1.0.4's manifest is **not merely misplaced, it is non-functional**. Its target declares `path: "Sources/open_file_ios"` (`open_file_ios-1.0.4/ios/open_file_ios/Sources/Package.swift:23`) relative to a package root of `ios/open_file_ios/Sources/`, i.e. `ios/open_file_ios/Sources/Sources/open_file_ios`, which does not exist; it also has `dependencies: []` and carries commented-out template TODOs (lines 22-34). So the baseline is a stub, not a near-miss.

---

## F4 — FlutterFramework integration: matches the prescribed 3.47 form

1.1.0's manifest (`open_file_ios-1.1.0/ios/open_file_ios/Package.swift:14-22`) is character-for-character the form the tool tells plugin authors to write (`darwin_dependency_management.dart:484-487`):

```
.package(name: "FlutterFramework", path: "../FlutterFramework")
.product(name: "FlutterFramework", package: "FlutterFramework")
```

The relative path resolves because the tool arranges siblings:
- plugins are symlinked into `relativeSwiftPackagesDirectory` = `ios/Flutter/ephemeral/Packages/.packages/<basename>` (`xcode_project.dart:170-178`, `swift_package_manager.dart:185-232`), basename carrying the version, e.g. `open_file_ios-1.1.0`;
- `flutterFrameworkSwiftPackageDirectory` is generated as a **sibling** at `.packages/FlutterFramework` (`xcode_project.dart:186-187`, `swift_package_manager.dart:403,422-446`).

Also relevant: `_getPluginDependencies` (`swift_package_manager.dart:307-333`) regex-matches `"../FlutterFramework"`, finds no *plugin* by that name, and `continue`s — so the rsync-copy-and-rewrite path (`_copyPluginAndUpdateManifest`, lines 341-395) is **not** triggered. The pub-cache package is symlinked verbatim. Clean.

Notable positive signal: `url_launcher_ios-6.4.1/ios/url_launcher_ios/Package.swift:18,22` has **no** FlutterFramework dependency — the older convention. open_file_ios 1.1.0 is ahead of several first-party plugins for 3.47.

**Unverified (cannot run anything):** whether SwiftPM resolves `../FlutterFramework` from the *symlink* path rather than the pub-cache realpath. The tool's own comment — *"Flutter plugins that support SwiftPM will be symlinked in this directory to keep all Swift packages relative to each other"* (`xcode_project.dart:175-177`) — plus the fact that the entire plugin ecosystem depends on it, makes this very likely correct, but it is a design expectation, not something I verified. The PRD is right to list it; keep it as a harness check.

---

## F5 — Podfile.lock: mandatory, not conditional; and a concrete regeneration hazard

The podspec `description` changed:
- 1.0.4 `ios/open_file_ios.podspec:9`: `A new Flutter project.`
- 1.1.0 `ios/open_file_ios.podspec:9`: `The iOS implementation of open_file.`

`SPEC CHECKSUMS` is the SHA1 of the podspec file, so `open_file_ios: 46184d802ee7959203f6392abcfa0dd49fdb5be0` (`Podfile.lock:235`) **will** change, and `pod install --deployment` (`.github/workflows/mobile-podfile-lock.yml:27`) will fail until the lock is regenerated. The PRD's *"podspec description checksum **if** regenerated"* should read *must*. Everything else in the podspec is unchanged — `s.version '1.0.3'`, `s.source_files 'open_file_ios/Sources/open_file_ios/**/*.{h,m}'`, `s.dependency 'Flutter'`, `s.ios.deployment_target '12.0'` — so exactly one line should move.

**Hazard the PRD does not cover:** regenerating Locker's `Podfile.lock` locally can drift lines unrelated to this change — most obviously `COCOAPODS: 1.17.0` (`Podfile.lock:253`) if your local CocoaPods differs, and potentially trunk-sourced pods. Pin CocoaPods 1.17.0, or restore unrelated lines and re-verify.

**Prerequisites to even reach `pod install` for Locker** (from `locker-build.yml:239-249` and the Podfile): `flutter pub get` (for `ios/Flutter/Generated.xcconfig`, required by `Podfile:14-24`), `cargo codegen frb locker` (for the `ente_locker_frb` pod), `dart run rive_native:setup --platform ios`, and the `EnteOnnxRuntime` podspec at `apple/packages/EnteOnnxRuntime/` (`Podfile:35`). Budget for this; the PRD's "<20 changed lines" understates the setup cost.

---

## F6 — SDK/OS floors

| | 1.0.4 | 1.1.0 |
|---|---|---|
| Dart SDK | `>=2.17.0 <4.0.0` | `^3.11.0` |
| Flutter | `>=1.20.0` | `>=3.41.0` |
| `Package.swift` platform | `.iOS("12.0")` | `.iOS("13.0")` |
| podspec `deployment_target` | `12.0` | `12.0` (unchanged) |

(`open_file_ios-1.0.4/pubspec.yaml:6-8` vs `1.1.0/pubspec.yaml:6-8`; `Package.swift:9` / `:13`.)

- CI pins Flutter **3.47.2** (`.github/actions/setup-flutter/action.yml:19`), Dart 3.13.2 (`/Users/aman/flutter/bin/cache/flutter.version.json`). Both constraints satisfied. ✔
- **No supported-OS change for Locker.** The podspec floor stays 12.0 and `Podfile:2,50` forces 15.1 anyway. The `.iOS("13.0")` only binds under SwiftPM, and `SwiftPackageManager.updateMinimumDeployment` (`swift_package_manager.dart:464-489`) raises the generated package to the project's deployment target; 13 ≤ 15.1. ✔ No Aman-level OS decision required.
- **Minor, worth a sentence in the PR:** `source-snapshot/mobile/pubspec.yaml:5` declares `sdk: ">=3.10.0 <4.0.0"`, but after this bump the workspace's true floor is Dart 3.11. Pub won't reject this today (it checks the *current* SDK against the package constraint, not the root's declared range), but anyone on 3.10 now fails `flutter pub get --enforce-lockfile` with a confusing message. Raising the declared floor is a maintenance call — flag it, don't bundle it.

---

## F7 — RootViewController / non-UIScene: reclassify, this is not new risk

I read both `OpenFilePlugin.m` files in full. **They are identical, 204 lines each**, including `RootViewController()` (lines 8-25) with the `connectedScenes` walk and the `nil` → `{"message":"the root view controller could not be found","type":-4}` path (lines 61-67). `OpenFilePlugin.h` is likewise identical (7 lines, both). `source-inspection.txt:6` reports the `ios/` map as differing only because `Package.swift` moved; the PRD's byte-identical claim holds for the sources that compile.

`CHANGELOG.md:3-4` attributes this to **1.0.4** ("Fix compatibility with UIScene"). Locker already ships 1.0.4 (`source-snapshot/mobile/pubspec.lock:1853`) with `enable-uiscene-migration: false`, a legacy `FlutterAppDelegate` (`source-snapshot/.../ios/Runner/AppDelegate.swift:5-13`), and an `Info.plist` with no `UIApplicationSceneManifest` (I read the whole file).

So the PRD's "Known uncertainty" is a **pre-existing property of shipped code, not a risk introduced by this bump**. Under CocoaPods the compiled output is bit-identical; there is no mechanism by which this change alters that behavior.

**Unverified:** whether `UIApplication.connectedScenes` yields the key window under Locker's non-UIScene lifecycle at runtime. Expected yes — UIKit creates an implicit `UIWindowScene` on iOS 13+ and the legacy `window` attaches to it — but I did not verify this in this repo and cannot run anything. The cheap decisive test is already available: **if it were false, Locker's file opening would be broken today on 1.0.4.** Establish that baseline first; it costs one tap and settles the question.

Keep the PRD's rule against silently enabling UIScene or patching vendor source. But downgrade this from a gate to a one-shot regression smoke.

---

## F8 — Adequacy of the acceptance checks

**Check 1 — sound.** Add one assertion: the `mobile/pubspec.lock` diff must touch *only* the `open_file_ios:` block (version + `sha256`). The frozen-pubspec checker will not catch collateral transitive drift (F2), so this must be eyeballed.

**Check 2 — the only check that can substantiate the SwiftPM claim. Three gaps:**
- The harness must be created *without* the `enable-swift-package-manager: false` guard, and should pin exactly `open_file: 3.5.11` and nothing else — other plugins in a realistic dep set (e.g. `url_launcher_ios 6.4.1`, F4) lack the FlutterFramework dependency and would produce unrelated failures that muddy the result.
- To be Locker-representative it should *also* set `enable-uiscene-migration: false` and keep a legacy `FlutterAppDelegate`. Note `flutter create` on 3.47 and the package's own example produce the newer form (`open_file_ios-1.1.0/example/ios/Runner/AppDelegate.swift:5-15`, `FlutterImplicitEngineDelegate` + `didInitializeImplicitFlutterEngine`), which is **not** representative — the PRD's own rule in check 3 rejects exactly this, but check 2 doesn't say how to avoid it.
- "Absence of target CocoaPods fallback" is concretely checkable: inspect the generated `ios/Flutter/ephemeral/Packages/FlutterGeneratedPluginSwiftPackage/Package.swift` for the `open_file_ios` package dependency and the `open-file-ios` product target dependency (`swift_package_manager.dart:216-229` — note the hyphenated product name), and confirm `open_file_ios` is absent from the harness `Podfile.lock` (mechanism: `podhelper.rb:327-330`).

**Check 3 — mis-scoped.** It bundles (a) SwiftPM runtime proof, which belongs in the harness, with (b) Locker regression, which per F7 is provably unchanged. Split them. Also: "device archive may be replaced by simulator build locally" is fine, but see the next point for why the archive path matters later.

**Check 4 — fine but low-signal.** `file_util_test.dart` is pure Dart (I read its setup and first case; it exercises `prepareOpenFileForTest` handoff naming/copying, `file_util.dart:440-506`) and cannot be affected by a native-only bump. Run it as hygiene, don't present it as evidence.

**Check 5 — fine.** The publication gate ("publish only if native acceptance holds") is worth a sanity check: it conditions a zero-runtime-effect change on a harness result. I'd keep it for evidence value, but be explicit that the harness proves *package readiness*, not *Locker behavior*.

---

## A finding for whoever eventually lifts the guard (out of scope here, but it changes the framing)

Locker's release pipeline invokes **`xcodebuild archive` directly on `ios/Runner.xcworkspace`** (`locker-build.yml:267-283`), not `flutter build ipa`. `SwiftPackageManagerIntegrationMigration` — which injects `FlutterGeneratedPluginSwiftPackage` into `project.pbxproj` and the scheme — runs only from the `flutter build`/`flutter run` iOS path (`ios/mac.dart:166-174`). So under a bare `xcodebuild` release, plugins would be dropped from CocoaPods (`podhelper.rb:330`) and never wired into SwiftPM.

That is very likely the concrete reason `enable-swift-package-manager: false` exists ("Remove after CI and Xcode support SwiftPM"), and it is the hard blocker for enablement — harder than the plugin bumps. Mentioning it in the PRD would make this pilot's sequencing legible.

---

## Smallest source-grounded path

1. In the worktree, resolve `open_file_ios` only — `dart pub upgrade open_file_ios` (or equivalent), **not** a hand-edited lock. The `sha256` must be generated, not typed. Expect one block changed in `mobile/pubspec.lock`.
2. `flutter pub get --enforce-lockfile` from `mobile/`; confirm no other package moved.
3. Prereqs (F5) → `pod install` in `mobile/apps/locker/ios` with CocoaPods 1.17.0 → confirm the diff is exactly the one `open_file_ios` `SPEC CHECKSUMS` line → `pod install --deployment` exits 0.
4. Harness proof per F8/check 2, kept in the evidence folder, outside the product diff.
5. One simulator smoke of Locker file opening as regression evidence (and to settle F7's baseline question).
6. Fix the commit message per F1.

Total product diff: 2 files, ~3 changed lines. The PRD's scope is right; its *claim* is what needs narrowing.

---

## Open questions

1. **Is the commit subject negotiable?** "Enable SwiftPM support for Locker file opening" is factually wrong given F1. I'd change it, but the PRD presents it as proposed wording and the PR body is to be empty — so this needs a decision, not an assumption.
2. **Should `mobile/pubspec.yaml`'s declared `sdk: ">=3.10.0 <4.0.0"` be raised to `>=3.11.0`?** (F6.) Maintenance call; I'd leave it and flag it in the PR rather than widen the diff.
3. **What is the actual gating item for lifting the guard** — the bare-`xcodebuild` archive path, UIScene migration, or the long tail of CocoaPods-only plugins (`Podfile.lock` still lists `app_links`, `camera_avfoundation`, `file_picker`, `flutter_secure_storage`, `fluttertoast`, `listen_sharing_intent`, `rive_native`, `sentry_flutter`, and the first-party `ente_*` plugins)? This determines whether a five-package plugin-bump pilot is the right lever at all.

---

## Evidence gaps and caveats on my sources

- **`mobile/apps/locker/ios/Podfile.lock` is not in `evidence/source-snapshot/`.** It is one of the two files the PRD proposes to change. I read it from the **primary checkout**, which the task states is older than `08d10562`. Every structural conclusion in F5 should be re-derived against `origin/main` before implementing. This is the one gap I'd close first.
- `/Users/aman/flutter` reports `frameworkVersion 3.47.2` / `dartSdkVersion 3.13.2` on channel `[user-branch]`, with `bin/internal/release-candidate-branch.version` = `flutter-3.47-candidate.0`. The framework version matches the CI pin exactly, so I treated its `flutter_tools` sources as authoritative for 3.47.2; strictly, it is a user-branch checkout and could differ from the released stable tag in minor ways.
- I did not compute hashes. "Byte-identical" for `OpenFilePlugin.m`/`.h` (F7) means I read both files in full and compared their contents; the PRD's SHA256 verification of the archives is separate and I did not reproduce it.
- I verified nothing at runtime, and nothing about actual SwiftPM path resolution, compilation, linking, or simulator behavior. Every such statement above is labeled as expectation.