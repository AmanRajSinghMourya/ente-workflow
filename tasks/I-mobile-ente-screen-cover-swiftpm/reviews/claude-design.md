I read the PRD, the plugin, its three consumers, the workspace/app pubspecs, both CI workflows, and the Flutter 3.47.2 tooling in `/Users/aman/flutter`. Below is what the sources actually establish, what the plan gets right, and the four things I think can bite.

## Confirmed constraints (these pin the manifest exactly)

The generated app package is built by `SwiftPackageManager._dependenciesForPlugins` (`/Users/aman/flutter/packages/flutter_tools/lib/src/macos/swift_package_manager.dart:169-230`), and it hardcodes three names:

- **Package name** → `.package(name: plugin.name, path: …)` (line 217) ⇒ must be exactly `ente_screen_cover`.
- **Product name** → `.product(name: plugin.name.replaceAll('_','-'), packageName: plugin.name)` (line 224-229) ⇒ must be exactly `ente-screen-cover`.
- **Target name** → the ObjC registrant already committed at `mobile/apps/locker/ios/Runner/GeneratedPluginRegistrant.m:33-37` does `#if __has_include(<ente_screen_cover/EnteScreenCoverPlugin.h>) … #else @import ente_screen_cover;`. There is no such header, so the `@import` branch is taken under **both** package managers, and the Swift module name must be `ente_screen_cover` ⇒ target name `ente_screen_cover`. A useful consequence: **the registrant is byte-identical under CocoaPods and SwiftPM**, so no registrant churn should appear in the diff. If it does, something is wrong.

Discovery path is `plugins.dart:449-485`: `<plugin_root>/ios/<package_name>/Package.swift`, i.e. `mobile/packages/screen_cover/ios/ente_screen_cover/Package.swift`. The PRD's layout is correct.

**FlutterFramework dependency is correct and the relative path does resolve.** `flutterFrameworkSwiftPackageDirectory` is `ios/Flutter/ephemeral/Packages/.packages/FlutterFramework` (`xcode_project.dart:186`), and plugin symlinks are created as siblings in `…/Packages/.packages/` (`swift_package_manager.dart:207`), so `"../FlutterFramework"` from the plugin package root lands on it. Also note `_getPluginDependencies` (`swift_package_manager.dart:307-333`) regex-matches `"../FlutterFramework"`, finds no plugin by that name, and returns empty — so the plugin is **symlinked in place, not rsync-copied**, and the manifest is used verbatim. Good.

One thing the PRD doesn't mention: the symlink basename is `_fileSystem.directory(plugin.path).basename` (line 188) = `screen_cover`, not `ente_screen_cover`, so the generated dependency will read `.package(name: "ente_screen_cover", path: "../.packages/screen_cover")`. Directory ≠ package name is the *normal* upstream case (pub-cache dirs are `name-version`), so I rate this low-risk, but it's worth eyeballing once in the generated graph rather than assuming.

## Floor preservation — the template will silently raise your floor

`FlutterDarwinPlatform.ios.deploymentTarget()` is `Version(15, 0)` in this Flutter (`darwin/darwin.dart:77-82`), and `create.dart:1011` feeds that into `{{iosSupportedPlatform}}`. **Rendering the template verbatim yields `.iOS("15.0")`, not 13.0.** Since the podspec is `s.platform = :ios, '13.0'`, using the template as-is would raise the plugin's SwiftPM floor above its CocoaPods floor. The PRD says iOS 13, which is right — just make sure the implementation deliberately overrides the template default rather than inheriting it.

Confirmed app floors, unchanged by this work: Photos 15.1, Locker 15.1, Auth 15.0 (Podfiles + pbxproj; Photos additionally has an 18.4 extension target). A 13.0 plugin floor under a 15.x top-level package is legal (dependency floor must be ≤ top-level). Every API the plugin uses — `connectedScenes`, `UIBlurEffect(.systemMaterial)` — is iOS 13+, so 13.0 also compiles cleanly.

`format()` emits the string form `.iOS("13.0")` (`swift_packages.dart:226-232`); existing repo manifests (`mail/ios/Package.swift`, `ente_photos_platform/ios/Package.swift`) use the enum form `.iOS(.v13)`. Both parse to the same value — pick one, but validate the **parsed** value, not the literal text (see below).

## Dual CocoaPods compatibility — safe here, for a specific reason

`podhelper.rb:327-334` skips a pod entirely when `swift_package_manager_enabled && Package.swift exists`. Since `swiftPackageManager` is `enabledByDefault: true` on stable (`features.dart:233-240`), that skip would normally fire the moment you add the manifest — and it would drop `ente_screen_cover` from all three Podfile.locks, breaking `pod install --deployment`.

It does not fire here, because the guard is complete: `enable-swift-package-manager: false` is set in **all four** pubspecs — `mobile/pubspec.yaml:12`, `apps/photos/pubspec.yaml:286`, `apps/locker/pubspec.yaml:111`, `apps/auth/pubspec.yaml:152`. Project-level config is read from the current project's manifest (`flutter_features_config.dart:104-146`), so the guard holds regardless of which directory Flutter is invoked from. The on-disk `mobile/apps/locker/.flutter-plugins-dependencies` confirms `"swift_package_manager_enabled":{"ios":false,"macos":false}` on Flutter `3.47.2`. So the pod keeps being installed and the lock entries stay.

Two consequences worth stating plainly:

1. **The Podfile.lock churn is certain, not conditional.** `SPEC CHECKSUMS` is the SHA1 of the podspec file, and you are editing `s.source_files`. All three locks (`photos`, `auth`, `locker`, currently all `6792566774f1c83939f9c1d03ed0a1f1ded45ae4`) must change in the same PR or `mobile-podfile-lock.yml` fails. The PRD's "only if deployment checks require it" should be read as "will be required".

2. **Inside this repo the manifest is inert.** No app consumes it via SwiftPM. So the only line in this PR that can break production is the podspec glob — which makes it the thing to review hardest, and makes the external harness (A2) the only real proof the manifest works.

On that glob: use the upstream-canonical `s.source_files = 'ente_screen_cover/Sources/ente_screen_cover/**/*'` (`templates/plugin_darwin_spm/darwin.tmpl/projectName.podspec.tmpl:17`). Do **not** shorten it to `ente_screen_cover/**/*` — that would sweep `Package.swift` into the pod target, and compiling a `import PackageDescription` file into the app is a hard build failure. Confining the glob to `Sources/` is what keeps the two systems on one source tree without collision.

## Validation sufficiency

**A2 has a concrete blocker you should hit before writing the manifest.** `mobile/packages/screen_cover/pubspec.yaml:4` declares `resolution: workspace`. An external harness app cannot necessarily `path:`-depend on a workspace member; pub is likely to reject it. Resolve this first, because it determines the whole A2 approach:

- *Option A (preferred if pub accepts):* harness outside the repo, direct `path:` dependency on the real package.
- *Option B:* harness inside `mobile/` as a workspace member with `flutter: config: enable-swift-package-manager: true` in the harness's own pubspec (project-level config beats the root's `false`). **But** this mutates `mobile/pubspec.yaml`'s workspace list and `mobile/pubspec.lock`, which breaks both A5 checks (`frozen-pubspecs/check.rb:121-125` walks the workspace member list, and `flutter pub get --enforce-lockfile`) and violates A6. If you take this route, do it in a throwaway copy of the checkout, never in the implementation worktree.
- *Option C:* copy the package outside the workspace with only the `resolution:` line removed, and record the one-line diff plus a hash of the `ios/` tree to show source identity.

**A1 should use `swift package dump-package`, not text matching.** Flutter itself parses plugin manifests this way (`build_swift_package.dart:1008-1014`), it runs offline without `../FlutterFramework` present, and it gives you `name`, `platforms`, `products`, `dependencies`, `targets` as JSON. That makes the A1 assertions (name `ente_screen_cover`, product `ente-screen-cover`, target `ente_screen_cover`, iOS 13.0, one `fileSystem` dependency with identity `flutterframework`) mechanical and form-agnostic.

**A5 will not exercise the plugin at all.** I grepped `packages/lock_screen/test/` — nothing references the method channel or `setHideAppContent`. The Dart suite proves nothing about this change; treat A2/A3 as the only real evidence, which is what the pilot PRD's check 4 already demands.

**A3's comparison is only meaningful if both legs run on the same simulator OS.** Also, pre-scope two behaviors so a baseline/migrated diff isn't misread as a regression: the live frame visible *during* the swipe-up gesture (the overlay is added on `didEnterBackground`, after the gesture begins), and Control Center / notification-shade pulldown, which fires only `willResignActive` and therefore produces no blur. Both are pre-existing and out of scope; note them rather than "fix" them under a packaging PR.

## Legacy AppDelegate + `connectedScenes`

All three apps use the legacy lifecycle: `@main class AppDelegate: FlutterAppDelegate` with `GeneratedPluginRegistrant.register(with: self)` and **no `UIApplicationSceneManifest` in any Info.plist** (I grepped all three; zero matches for `scene`), plus `enable-uiscene-migration: false` in all four pubspecs. Packaging does not touch any of this.

The substantive question is whether `keyWindow()` (`EnteScreenCoverPlugin.swift:64-69`) still finds a window. On iOS 13+ UIKit vends an implicit `UIWindowScene` even for non-scene apps, so `connectedScenes` is non-empty — the lookup works today, which is why the feature ships. Two real risks, both orthogonal to SwiftPM but directly in A3's path:

- `first { $0.isKeyWindow }` can return `nil` if no window is key at the moment `didEnterBackgroundNotification` fires (e.g. a system alert or another window holds key). `showOverlay` then silently returns and **no blur is applied** — a privacy failure with no error surface. Worth one deliberate probe rather than assuming.
- CI runs `macos-26`. On iOS 26, the legacy (non-`UIScene`) lifecycle is deprecated and runs through a compatibility shim. Whether that shim still populates `connectedScenes` the same way on the simulator you test is the single most important thing A3 should establish — and it's a *baseline* property. If the CocoaPods baseline leg fails on iOS 26, that is not a packaging regression; per the PRD, stop and escalate rather than adjusting the lifecycle to make a test pass.

## Smallest decisive checks

1. `flutter pub get` in a scratch harness with a `path:` dep on the real package — decides the entire A2 strategy in one command, before any code is written.
2. `swift package dump-package` in `ios/ente_screen_cover/` — validates the manifest offline, no Xcode, no FlutterFramework.
3. In the harness after `flutter build ios --simulator --config-only`: read `ios/Flutter/ephemeral/Packages/FlutterGeneratedPluginSwiftPackage/Package.swift` for `.package(name: "ente_screen_cover", path: "../.packages/screen_cover")` + `.product(name: "ente-screen-cover", …)`, confirm `.packages/screen_cover` is a symlink into the real repo (not an rsync copy under `SourcePackages/`), and confirm `Pods/` contains **no** `ente_screen_cover` — that last one is the proof against CocoaPods fallback.
4. On the simulator, with the cover enabled: background, inspect the switcher card for blur, foreground and confirm removal; repeat enable→disable→background (expect no blur) →re-enable. Then the `nil`-key-window probe.
5. `pod install --deployment` in all three app `ios/` dirs after updating the three checksums — and confirm `ente_screen_cover` is still listed as a pod in each lock, which is the assertion that the `enable-swift-package-manager: false` guard held.

## Must be verified before publication

- Harness build log and generated package graph showing the plugin linked via SwiftPM, with no pod of the same name installed (A2).
- Real channel `enable`/`disable` exercised through the harness, not a mock.
- Baseline **and** migrated app-switcher privacy runs on the same simulator OS, both recorded (A3). No PR if the baseline leg fails — escalate.
- The retained CocoaPods leg still builds and runs, with a byte-identity check that both systems select the same `EnteScreenCoverPlugin.swift` (A4).
- All three `Podfile.lock` checksums updated and all three `pod install --deployment` runs green.
- Diff contains: relocated Swift source, new `Package.swift`, one podspec line, three lock checksums — and nothing else. Specifically confirm no `GeneratedPluginRegistrant.*`, no pbxproj, no `.flutter-plugins-dependencies` (gitignored, `mobile/.gitignore:20`), no pubspec/lock, no harness files leaked in.
- Recorded statement that the plugin's SwiftPM floor is 13.0 (not the template's 15.0) and that app floors 15.1/15.1/15.0 are untouched.

One judgment call I'd flag for Aman rather than decide here: because all four pubspecs disable SwiftPM, this PR delivers no behavior change to any shipping app — it only prepares the plugin and, in doing so, edits the one file (the podspec) that the shipping builds actually use. That tradeoff is inherent to the staged-adoption plan and I think it's the right one, but it's worth being explicit that the risk and the benefit land in different places.