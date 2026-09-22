I ignored the trailing Python snippet — it would have executed `checks.py`, deleted/rewritten `reviews/design-command*.json` and written a receipt file, which your read-only constraint forbids. Everything below is from read tools on the clean checkout `6393d856` plus the evidence folder, the installed Flutter 3.47.2 SDK, and `~/.pub-cache` (read-only).

## Verdict

A dependency-only 9.1.0 bump is behavior-preserving for **every Ente call site except one**, and the SwiftPM part is **inert in the shipped apps today**.

- **iOS: provably unchanged.** The Obj-C sources are content-identical after the move, and `mobile/pubspec.yaml:11-13` plus `apps/{photos,auth,locker}/pubspec.yaml:286/152/111` set `enable-swift-package-manager: false`, so all three apps keep consuming the podspec. 9.1.0 changes *where* the files live, not what compiles.
- **Dart: unchanged** (`Color.value` → `toARGB32()` is a literal no-op, see below), except the FToast stale-context path.
- **Android: one real delta** — `apps/photos/lib/ui/viewer/file/video_widget.dart:198` on API 26–29. That is the single product decision.

## Source facts verified

**iOS native is a pure move.** `ios/Classes/{FluttertoastPlugin,UIView+Toast}.{h,m}` → `ios/fluttertoast/Sources/fluttertoast/*.m` + `include/fluttertoast/*.h`; `ios/Resources/PrivacyInfo.xcprivacy` → `Sources/fluttertoast/PrivacyInfo.xcprivacy`. I read `FluttertoastPlugin.m` (143 lines) and `FluttertoastPlugin.h` (4 lines) and `PrivacyInfo.xcprivacy` (14 lines) in both versions: identical. `UIView+Toast.h`: identical (446 lines). `UIView+Toast.m`: 521 non-blank lines in both, and all ~90 structural anchors (`#import`, every `- (`/`+ (`/`@implementation`/`static`/`objc_*AssociatedObject`) land on **identical line numbers** in both. Caveat: with read-only tools I cannot hash, so "byte-identical" is PRD assertion; "content-identical at line granularity" is what I verified.

**`toARGB32()` is a no-op, not a risk.** `/Users/aman/flutter/bin/cache/pkg/sky_engine/lib/ui/painting.dart:230`: `int get value => toARGB32();`. Same packing, same `_floatToInt8` rounding. Ente's toast colors are plain sRGB `Color.fromRGBO` (`packages/ui/lib/theme/ente_theme_data.dart:387-393`, `colors.dart:728-729`). Zero channel-value delta on the method channel.

**9.1.0's Package.swift matches this exact toolchain.** `flutter_tools/lib/src/macos/darwin_dependency_management.dart:482-487` requires literally `.package(name: "FlutterFramework", path: "../FlutterFramework")` + `.product(name: "FlutterFramework", package: "FlutterFramework")`; `plugins.dart:458-477` expects the manifest at `<plugin>/ios/<name>/Package.swift`. 9.1.0 satisfies both. `.iOS("13.0")` is below the app floors (`apps/photos/ios/Podfile:2` and `locker` = 15.1, `auth` = 15.0) → no OS-support change.

**Toolchain fits.** Installed and CI Flutter are both 3.47.2 / Dart 3.13.2 (`bin/cache/flutter.version.json`, `.github/actions/setup-flutter/action.yml:19`) vs 9.1.0's `sdk >=3.11.0`, `flutter >=3.41.0`.

**Real Ente call sites** (only 5 production files import the package): `packages/ui/lib/utils/toast_util.dart:14-47`, `apps/auth/lib/utils/toast_util.dart:35-105`, `packages/ente_components/lib/components/toast_component.dart:17-40`, `apps/photos/lib/ui/notification/toast.dart:17-30`, `apps/photos/lib/ui/viewer/file/video_widget.dart:198`, plus the three internal-user home-widget services (`memory/people/album_home_widget_service.dart:229/283/450`) and `integration_test/video_editor_test.dart:623`.

Two facts the PRD does not state that materially narrow the blast radius:
- `apps/photos/lib/ui/notification/toast.dart:17` gates the native toast on `Platform.isAndroid`; iOS Photos uses EasyLoading. So Photos' themed toast is Android-only.
- Auth's native path is only reached when `!PlatformDetector.isMobile()` (`toast_util.dart:16-18`), i.e. desktop, where the plugin throws `MissingPluginException` and falls back to FToast. **Auth never executes the Android native toast**, so Auth's minSdk 24 is irrelevant to the gravity change.

## The one product decision: Android 26–29 plain toast

`MethodCallHandlerImpl.kt:96-112` now wraps `setGravity` in `if (bgcolor != null)`. Every Ente native call passes a non-null `backgroundColor` **except** `video_widget.dart:198` (`Fluttertoast.showToast(msg: "Failed to download preview!")` — user-visible, not internal-user-gated). On iOS the Dart layer defaults `backgroundColor` to black (`lib/fluttertoast.dart:98-103`), so iOS is unaffected. On Android ≥30 `setGravity` is already ignored for text toasts. Photos `minSdk = 26` (`apps/photos/android/app/build.gradle:76`) ⇒ the toast moves from *bottom + 100px* to the OS default y-offset on **Android 8.0–10 only, for that one string**. Real, small, and not behavior-preserving in the strict sense → Aman's call.

Every "fix" carries its own cost, so none should be taken automatically:
- Passing `backgroundColor` converts a system toast into an inflated custom toast on **all** Android versions and changes its look — not a neutral compatibility patch.
- Routing line 198 through `showToast(context, …)` also changes iOS (EasyLoading) and adds theme styling.
- Fork-patching `setGravity` back for API<30 means owning a fork of the Android source, i.e. a maintenance decision.
- Staying on 8.2.14 and carrying a local SwiftPM patch is also fork ownership; 10.0.0 is out of scope.

My recommendation: **accept and document**, because the only affected string is a transient failure notice on three now-minority API levels; the cheapest alternative (option 2) is a strictly larger visual change.

Secondary, non-shipping: `video_editor_test.dart:626` passes `ToastGravity.TOP` with no background color, so its annotation loses TOP on API<30. Integration-test-only; not user-visible.

## FToast queue / dismiss / stale context

`lib/fluttertoast.dart:180-191` re-enables the `context?.mounted != true` guard. Consequences for Ente:

- Happy path is untouched: `_getPositionWidgetBasedOnGravity`, the keyboard BOTTOM→CENTER swap (`:277-281`), `positionedToastBuilder` precedence, `removeCustomToast`, `removeQueuedCustomToasts`, `_ToastStateFul` tap/fade are all byte-for-byte the same. Auth's positioned + tap-dismiss overlay, the shared `MissingPluginException` fallback, and the ente_components banner's `removeQueuedCustomToasts()`-then-show replacement semantics are unchanged.
- Every Ente site calls `init(context)` immediately before `showToast`, so the context is fresh at request time. The guard only fires for a *queued* toast whose screen was popped before `removeCustomToast()` re-entered `_showOverlay()`. Auth is the only site that can queue more than one (ente_components clears first).
- In that window the behavior does change: baseline hits the deactivated-ancestor assert inside `Overlay.of`, gets swallowed by `catch (err)` (`:193-203`), clears the queue and then throws the misleading `"Error: Overlay is null"` string from a timer callback; candidate prints in debug and drops silently. In release (asserts off) the baseline could still have shown the toast via a surviving ancestor overlay, where the candidate drops it. Net: strictly fewer spurious errors, one theoretically droppable queued toast. I'd classify this as a bug fix, but it is a behavior change and should be stated in the PR, not glossed as "no change".
- One edge worth a widget test rather than reasoning: the new branch calls `removeQueuedCustomToasts()`, which does `_entry?.remove()`; if `_entry` ever belonged to a disposed `OverlayState`, `remove()` → `markNeedsBuild` could throw. In practice `_entry` is null on that path, but prove it.

## The new flag and timer (unneeded, but don't patch it)

`Fluttertoast.isCurrentlyShowingToast` (`:51`, `:57`, `:120`, `:171`, `:216`, `:244`) is dead code for Ente — no repo reference. The one non-cosmetic addition is `:125-127`: **every native `showToast` now schedules a `Future.delayed(Duration(seconds: timeInSecForIosWeb))`**. In production that is one harmless extra 1-second timer per toast (the flag itself is wrong anyway — `LENGTH_LONG` outlives it). Two practical notes:

1. It is *not* reached when the channel is unimplemented, because it sits after the `await` that throws — so Ente's existing `MissingPluginException` fallbacks are unaffected.
2. Any new test that *mocks* the channel successfully must advance 1s (`await tester.pump(const Duration(seconds: 1))`), or the widget test fails with a pending timer. This is the only way this change can bite CI.

Do not "fix" the flag or timer: that is an upstream behavior change for other consumers plus fork maintenance, for zero Ente benefit. Also, do not adopt the flag in Ente code.

## Android build compatibility (risk downgraded, with precedent)

Effective deltas when the module is built inside an Ente app: `compileSdkVersion 33→36`, Java/Kotlin target `11→17`, and the re-added manifest `package` attribute. The `buildscript` AGP 8.13.0 / Gradle 8.13 / Kotlin 2.1.20 declarations in `android/build.gradle:4-16` and `gradle-wrapper.properties` only matter for the plugin's standalone example — 8.2.14 declares AGP 7.1.3/Kotlin 1.7.0 there **today** and Ente builds fine, which is the precedent that settles it.

- `compileSdk 36` == the app's (Flutter 3.47.2 default is 36, `FlutterExtension.kt:23`), so `detectLowCompileSdkVersionOrNdkVersion` stays quiet; android-36 is already required by `apps/photos/plugins/ente_background_manager/android/build.gradle:21`.
- Java 17 is already mandatory: `DependencyVersionChecker.kt:99-109` errors below JDK 17 / AGP 8.11.1 / KGP 2.2.20, and Ente is on AGP 8.12.1 + KGP 2.2.20 (`apps/*/android/settings.gradle:21-22`) with Gradle 8.14.3.
- The manifest `package=` is **not** an AGP 8 blocker in this configuration, and I can show it rather than assert it: `home_widget 0.8.0` (pinned at `apps/photos/pubspec.yaml:127`) ships `<manifest package="es.antonborri.home_widget" />` with `namespace` in its build.gradle (`android/build.gradle:29-30`), as do `share_plus 12.0.0`, `sentry_flutter 9.6.0`, `permission_handler_android`, and ~40 more in the current cache — and Photos builds today. fluttertoast's `package` equals its DSL namespace, which is the precedented-safe shape. Still confirm with a real build; the equal-vs-different distinction is what makes it safe, and I'm inferring AGP's rule from precedent, not from AGP source.

## Resolution / lockfile mechanics

Four pins (`apps/photos/pubspec.yaml:124`, `apps/auth/pubspec.yaml:88`, `packages/ui/pubspec.yaml:26`, `packages/ente_components/pubspec.yaml:13`) + one shared lock entry (`mobile/pubspec.lock:1153-1160`, needs the new sha256). `checks/frozen-pubspecs/check.rb` requires exact strings matching the lock, so all four must move together. Three findings:

1. **There is a fourth Podfile.lock**, not three: `packages/ente_components/example/ios/Podfile.lock:18` carries the same `fluttertoast: 2c67e14…` checksum, and `example` is a workspace member (`mobile/pubspec.yaml:33`). CI (`mobile-podfile-lock.yml:25`) only verifies photos/auth/locker, so leaving it stale is silent inconsistency. Regenerate it too, or say explicitly that you didn't.
2. All four locks say `COCOAPODS: 1.17.0`. Use exactly 1.17.0 locally or you'll rewrite that line in all of them.
3. The pod name and module name are unchanged, so the committed pod framework list in `apps/photos/ios/Runner.xcodeproj/project.pbxproj:657` (and `:753`) should be untouched — worth asserting that `pod install` leaves the pbxproj clean.

**Toolchain floor, flagged not blocking:** 9.1.0 requires Dart ≥3.11.0 while every Ente mobile pubspec declares `sdk: ">=3.10.0 <4.0.0"`. Pub validates against the *running* SDK, so `pub get --enforce-lockfile` passes on Dart 3.13.2 and CI stays green — but the effective floor rises to 3.11 without the declaration saying so. The flutter floor is already fine (`ente_components` declares `>=3.44.0`). Raising the `sdk:` bounds is a support decision; my recommendation is to leave them and note it in the PR rather than churn ~40 pubspecs.

## Evidence gap in candidate.diff

`candidate.diff` is a curated diff of shared files only. It omits: 9.1.0 **adds** root `ErrorSolvedTesting.dart` (a stray demo app for the new flag — outside `lib/`, so never compiled or analyzed by consumers), **removes** `fluttertoast.iml`, and rewrites `example/` (Gradle KTS, new `example/ios/Runner/SceneDelegate.swift`). All inert for Ente, but the diff shouldn't be cited as the complete delta. I separately confirmed `android/gradle.properties`, `android/settings.gradle`, and `FlutterToastPlugin.kt` are identical across versions, and that the dependency list is unchanged.

## Smallest viable path

1. Bump the four pins + the shared lock entry. Refresh **four** Podfile.lock checksums (or three plus an explicit note). **Zero Ente source edits.** Do not touch `enable-swift-package-manager` anywhere in the repo — SwiftPM proof belongs in a throwaway external harness, since the shipped apps remain CocoaPods and the acceptance line about "candidate SPM" can only be met there.
2. Leave `video_widget.dart:198` alone pending Aman's decision; if he wants the gravity preserved, that becomes a separate, explicitly-scoped change.
3. Estimated diff: four one-line pin changes + lock entry + four checksum lines + tests. Well under the 250-line estimate.

## Concrete baseline/candidate tests

Dart/widget (add, run on both 8.2.14 and 9.1.0):
- **Channel argument preservation** — mock `PonnamKarthik/fluttertoast` via `TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger.setMockMethodCallHandler`, call `ente_ui showToast`, assert the exact map: `msg`, `length: "long"`, `time: 1`, `gravity: "bottom"`, `bgcolor`/`iosBgcolor` == `0xF2181818`, `textcolor`, `fontSize: 16.0`, and that `cancel` is invoked first. This pins the `toARGB32` equivalence numerically. Remember `await tester.pump(const Duration(seconds: 1))` for 9.1.0's new timer.
- **Photos platform split** — assert `apps/photos/.../toast.dart` invokes the channel on Android and not on iOS (`debugDefaultTargetPlatformOverride`).
- **Mounted FToast queue/dismiss/position** — `packages/ente_components/test/components/toast_component_test.dart`: one banner visible, second call replaces rather than stacks, tap dismisses, `Positioned.bottom == viewPadding.bottom + Spacing.xl`. Must pass identically on both versions.
- **Auth positioned overlay** — `mobile_bottom_margin` + keyboard inset math and tap-dismiss removes both active and queued. Identical on both.
- **Stale-context clearing** — queue two toasts from a route, pop it, pump: candidate must not throw and must leave the queue empty. This *fails on 8.2.14 by design* — label it as the documented delta, not as a regression guard.

Native (cannot be replaced by mocks):
- Android **API 29 emulator** and a current API 36 device: baseline vs candidate for (a) `bgcolor != null` TOP/BOTTOM/CENTER — must be pixel-identical, (b) the plain `showToast(msg:)` path — expect and photograph the 26–29 shift, (c) `cancel()` mid-toast, (d) rapid replacement. Build all three apps (`photos` flavors, `auth`, `locker`) to confirm the manifest `package` attribute and compileSdk 36 / Java 17 resolve under AGP 8.12.1.
- iOS: baseline CocoaPods toast/cancel on all three apps after `pod install --deployment`; then a harness with SwiftPM enabled to prove linking, plugin registration, toast text/style/position/duration/cancel, that `FlutterFramework` resolves at the sibling path, and that the privacy manifest actually lands in the built app.

## Blockers and open items

- **Needs Aman (product):** the Android 26–29 plain-toast placement change at `video_widget.dart:198`. Everything else is routine.
- **Needs Aman only if it fails:** if the real Gradle build rejects the manifest `package` attribute despite the `home_widget`/`share_plus` precedent, the remaining options are all fork/maintenance choices — return with options, don't pick one.
- **Not yet verified from source (needs the harness):** SwiftPM link/registration/toast/cancel; privacy manifest presence in the built bundle; the four `pod install --deployment` runs; the three Android builds; that `pod install` leaves `project.pbxproj` untouched.
- **Decide before implementing:** the fourth Podfile.lock, and whether to leave the `sdk: ">=3.10.0"` declarations as-is.