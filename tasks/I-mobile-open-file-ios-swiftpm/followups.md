# Q003 saved-evidence observation

## Native harness batch — 22 September 2026

No findings. The baseline and candidate QuickLook screenshots show the same
`Locker handoff` title, both lines of original text, close control, search control
and share control. No visible clipping or candidate-only layout/content regression
appears in this captured state.

Build/device context supplied by the controller: official open_file 3.5.11 with
open_file_ios 1.0.4 through CocoaPods versus open_file_ios 1.1.0 through SwiftPM
without a Podfile.lock; generated Flutter harnesses using Locker's legacy
AppDelegate and no UIScene manifest; dedicated iPhone 17 Simulator on iOS 26.5
(38C73E90-17C6-4862-B92B-46770B6E07C7). Build configuration was not independently
audited by this observer.

The saved accessibility evidence confirms missing-file feedback
(`fileNotFound: the file does not exist。`), the title and exact original contents
in valid previews, and return feedback (`done: done`) for both builds. The initial
batch lacked the candidate missing-file and dismissal snapshots; the supplemental
candidate completion file closes that gap. It records `done: done` after dismissal,
a successful missing-file action on the same Simulator, and the resulting
`fileNotFound` screen. No finding results from these additional captures.

Evidence: [baseline preview](evidence/baseline-valid-handoff.png),
[candidate preview](evidence/candidate-valid-handoff.png),
[saved accessibility snapshots](evidence/maestro-native-evidence.json), and
[candidate completion snapshots](evidence/maestro-candidate-completion.json).
Expectation source: [PRD acceptance criteria](PRD.md) and
[native probe contract](evidence/native-plan.md).

Scope: package runtime observation only. This is not full Locker app verification,
a design comparison, or proof of persistence, permissions, accessibility operation
or race-free behavior. No follow-up task is proposed from these captures.

## Locker cached-file handoff batch — 22 September 2026

No findings. In the actual Locker Runner, the saved QuickLook preview shows the
fixture title `Locker Q003 original`, both original content lines, and a visible
Done action without clipping. The returned screenshot and accessibility snapshot
show `Returned; handoff content preserved`. The saved completion flow succeeds on
the same dedicated Simulator. These observations support the representative
Locker file-opening portion of PRD acceptance criterion 3 for this cached fixture.

The inspected external entrypoint creates `Locker Q003 original.txt` at Locker's
cached decrypted-file path, calls production `FileUtil.openFile(context, file)`,
awaits its return, and checks that a matching handoff file retains the fixture
contents. The supplied entrypoint contains no mocked file-opening channel.
[Native proof](evidence/locker-native-proof.json) records hashes for the production
file utility, native app configuration, pubspecs, external entrypoint and built
Runner artifacts; this observer has not independently audited those hashes.

The first saved dismissal attempt failed its returned-state assertion and left
QuickLook visible. The controller reports that the ID-based tap missed, then the
observed Done text selector succeeded and the entire flow passed again with an
animation wait. The saved eight-command success and final returned state confirm
recovery; these captures establish no product dismissal defect. Retain the failed
attempt as validation context.

Evidence: [Locker preview](evidence/locker-valid-handoff.png),
[returned state](evidence/locker-returned.png),
[initial handoff and failed assertion](evidence/maestro-locker-handoff.json),
[successful completion](evidence/maestro-locker-completion.json), and
[external entrypoint](evidence/locker_handoff_main.dart).

Scope: production Locker file utility and native preview through an external test
entrypoint using a prepared cached file. This does not exercise the normal
logged-in navigation, download/decryption journey, or other file formats. Locker's
platform chrome is not compared with the generated harness or treated as a design
regression. No follow-up task is proposed from this batch.
