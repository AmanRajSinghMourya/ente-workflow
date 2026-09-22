# SwiftPM: fluttertoast

**Deferred — cancelled by Aman on 22 September 2026.** Local task work is abandoned under the one-time cleanup request. The existing chat is archived; no restart or publication is authorized. Plans, reviews and historical evidence below are retained. Recovery: `/Users/aman/Documents/Codex/ente-recovery-20260922T075859Z`.

Queue: Q005. Host: local. Project: local-a0f48e7f2a6d317290c1ab9e6791ed49.
Assigned primary checkout: `/Users/aman/Development/ente-2`; never edit or switch it.
Chat: [Q005 · SwiftPM: fluttertoast](codex://threads/01a0c73b-4aa5-7d80-81cb-9471a564c1ff).

## Outcome and authorization

Adopt the minimum released fluttertoast SwiftPM support while preserving Photos,
Auth and Locker toast behavior, privacy resources, CocoaPods and supported OSes.
Candidate is 9.1.0 from current 8.2.14. No global SwiftPM/UIScene guard changes.
The 22 September batch authorization relayed in this task's opening delegation
from [coordinator](codex://threads/01a0c6ea-8e55-7c00-8798-52d124669141) supersedes
older hold/calibration text and routine plan/commit/publication gates. Target is
AmanRajSinghMourya/ente:main, ready PR through authenticated gh. Real user-visible,
support/security/data/maintenance decisions still need Aman. Do not force a PR.
Review sequence: source plan, persistent Claude design session, implementation and
checks, fork PR, extensive Claude review by exact same session ID, actual Codex bot
feedback. See [pilot PRD](../I-locker-swiftpm-pilot/PRD.md).

## Current code and source evidence

Investigation begins at 6393d8561a77e34654b16a8f9d0598cce6bb4557, clean branch
aman/locker-sync-fix. Four exact pins: mobile/apps/{photos,auth}/pubspec.yaml,
mobile/packages/{ui,ente_components}/pubspec.yaml; shared mobile/pubspec.lock.
Locker consumes the shared helpers transitively.

Hash-verified archives and extracted source are under evidence/fluttertoast-*
(external task folder; never patch pub cache). candidate.diff contains the actual
Dart/Android/build/podspec/manifest delta. Native iOS two .m files, two public .h
files and PrivacyInfo.xcprivacy are byte-identical after moves. New SPM manifest
uses Swift tools5.9, iOS13, FlutterFramework relative dependency and processed
privacy resource. Existing app floors Auth15.0, Photos/Locker15.1 are above it.
Candidate Dart>=3.11/Flutter>=3.41 fits the intended Flutter3.47.2 toolchain; verify
installed and latest main before implementation. Dependency list unchanged.
Fresh pub.dev and GitHub pub advisory APIs returned empty lists on22September.

Android changes AGP7.1.3→8.13.0, Kotlin1.7→2.1.20, SDK33→36, Java11→17;
app settings use AGP8.12.1/Kotlin2.2.20/Gradle8.14.3. Candidate also reintroduces
manifest package attribute. Validate build resolution; do not patch upstream or
raise app/toolchain floors silently.

Production native callers in shared UI, Auth desktop fallback, Photos wrapper,
and Photos home-widget service use nonnull backgroundColor and preserve gravity.
Photos video_widget.dart:198 calls Fluttertoast.showToast with only a message.
Candidate stops calling Android setGravity for bgcolor=null. Baseline sets BOTTOM
with yOffset100; candidate uses OS default. Android>=30 already ignores text-toast
gravity, but supported Photos Android26–29 may visibly differ. Need direct proof
and Claude assessment before treating this as behavior-preserving. The integration
video-editor TOP call also omits backgroundColor, so it loses TOP on Android<30.

Auth mobile helper uses FToast with keyboard/safe-area positioning and tap dismiss.
ente_components clears the singleton queue before banner toast; shared UI uses
FToast on MissingPluginException. Candidate clears pending overlays when the stored
context unmounts instead of attempting invalid ancestor lookup. Its new global
isCurrentlyShowingToast flag is unused by Ente. Existing valid mounted-context
queue, dismissal, positioning and fallback must pass unchanged.

## Technical plan and remaining decision

1. Obtain independent Claude technical review in a new persistent read-only session.
2. If behavior preservation remains viable, fetch main and create
   `.worktrees/I-mobile-fluttertoast-swiftpm` on `aman/mobile-fluttertoast-swiftpm`,
   with a single `.task` symlink here. Record immutable base. No edits to primary.
3. Establish baseline with acceptance-focused Dart/widget checks and external native
   harness. Compare 8.2.14 vs9.1.0 native Android custom TOP/BOTTOM, plain default,
   cancel/replacement; include Android29 for the changed setGravity path and current
   Android for real plugin registration. On iOS prove baseline CocoaPods native toast,
   candidate SwiftPM native linking/registration/toast/cancel and bundled privacy.
   Use harness-only SwiftPM setting, preserve app guards. Coordinate simulator
   ownership through shared pilot BOARD.
4. Only if no unresolved behavior/support/maintenance decision, update the four pins
   and relevant shared lock entry; refresh all four Podfile.lock checksums, including ente_components/example, as required.
   Add small meaningful consumer tests for native-channel argument preservation,
   mounted FToast queue/dismiss/position and stale-context queue clearing where feasible.
   Do not commit external harness/build artifacts. Estimated <250 lines plus lockfile.
5. Run frozen-pubspec check, flutter pub get --enforce-lockfile, relevant format/analyze
   and affected tests per mobile-lint.yml; verify four pod install --deployment runs (three apps plus components example)
   per mobile-podfile-lock.yml and affected Android builds. Record all failures and
   inherited blockers explicitly. Native proof cannot be replaced by mocked channels.
6. Preauthorized commit and ready PR title `[mobile] Add SwiftPM support for fluttertoast`,
   empty body, exact verified API/push identity, then same-session Claude code review
   and actual Codex bot feedback; refresh changed-SHA evidence on followups.

A real Android plain-toast placement change or inability to build upstream9.1.0
requires returning to Aman with source-grounded options. Adding a background color
changes system toast to custom toast, so it is not a neutral compatibility fix.
Do not choose a maintained fork, latest10.0.0, support drop or redesign automatically.

## Acceptance

- All consumer dependency resolution remains exact; no unrelated lock churn.
- iOS toast text/style/gravity/duration/cancel match baseline through candidate SPM;
  privacy resource is in the app bundle; no hidden CocoaPods supply of tested plugin.
- CocoaPods remains buildable and all four consuming lockfiles reproduce in deployment mode.
- Android supported versions preserve current relevant toast behavior and build with
  app settings; baseline vs candidate includes the plain Photos preview failure.
- Auth positioned/tappable overlays, shared fallback, and banner replace/dismiss work;
  screen disposal does not cause invalid ancestor lookup or stale pending overlay.
- Every final review/validation identifies exact source/PRD hashes and review SHA.

## Decision pending after Claude review

Status: needs decision. No implementation authorized for the discovered behavior delta.
Claude session `bef89a55-c360-42eb-aff9-24f92fc23c57` completed its design consultation;
[findings/dispositions](reviews/disposition.md) preserve exact reviewed PRD and evidence.
Primary and Claude recommend accepting system-default placement for the one unstyled
Photos preview-error toast on Android8–10, then continuing native validation with9.1.0.
Alternative: defer at8.2.14 to preserve exact current behavior. A packaging backport
fork would add ongoing maintenance; do not create it without an explicit decision.
No emulator runtime comparison or build success is claimed.

Sources: [9.1.0 release](https://pub.dev/packages/fluttertoast/versions/9.1.0),
[upstream](https://github.com/ponnamkarthik/FlutterToast),
[Android10 Toast implementation](https://android.googlesource.com/platform/frameworks/base/+/refs/tags/android-10.0.0_r1/core/java/android/widget/Toast.java),
[Android10 dimensions](https://android.googlesource.com/platform/frameworks/base/+/refs/tags/android-10.0.0_r1/core/res/res/values/dimens.xml).
Archive SHA256:8.2.14=90778fe0497fe3a09166e8cf2e0867310ff434b794526589e77ec03cf08ba8e8;
9.1.0=7903c9d5339173497bfecbc23bc4212f5a87e0edfac2e1693fb74465ea67da7e.
