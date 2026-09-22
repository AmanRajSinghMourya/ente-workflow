# Screen-cover evidence observations

## Baseline batch — 22 September 2026

Read-only observer review of the saved synthetic harness screenshots and native
lifecycle records. No observed bug, UX proposal, design mismatch or refactor
finding in this batch. The parent decides acceptance and publication readiness.

Build/run: CocoaPods baseline; primary source `6393d8561a`, with the native source
reported byte-identical to cached `origin/main` `cbdb06af06` in
[`evidence/baseline-native.md`](evidence/baseline-native.md). Flutter 3.47.2,
Xcode 26.6, iPhone 17 / iOS 26.5 Simulator,
`C9F0AAB3-EE28-4D0E-81B6-A3F471ED8878`. Legacy app lifecycle and synthetic fixture.
Expectation source: [PRD A3](PRD.md), preserving enabled background obscuring,
foreground removal, disable and re-enable behavior.

| Captured state and recorded action | Observed result | Evidence |
| --- | --- | --- |
| Enable twice, foreground | Fixture text and controls are readable; enabled status visible. Ready record has `coverCount=0`. | [Foreground](evidence/baseline-enabled-foreground.png) |
| Home then double Home, enabled | Switcher card is obscured; fixture text and controls are unreadable. Settled background record has `coverCount=1`. | [Enabled switcher](evidence/baseline-enabled-switcher.png) |
| Return from switcher | Readable foreground fixture restored, matching initial foreground state. Settled active record has `coverCount=0`. | [Resumed](evidence/baseline-resumed.png) |
| Disable twice, background/switcher | Fixture text and controls remain readable, with disabled status visible. Settled background record has `coverCount=0`. | [Disabled switcher](evidence/baseline-disabled-switcher.png) |
| Re-enable twice, background/switcher | Switcher card is obscured again; fixture text and controls are unreadable. Settled background record has `coverCount=1`. | [Re-enabled switcher](evidence/baseline-reenabled-switcher.png) |

Supporting interaction narrative: [baseline-native.md](evidence/baseline-native.md).
Native records: [baseline-lifecycle.jsonl](evidence/baseline-lifecycle.jsonl).
The screenshots agree with the settled native counts in the supplied sequence.

Evidence limits, not defect findings:

- This batch is before migration. It cannot establish migrated SwiftPM parity or
  native registration/linking; compare the matching migrated batch separately.
- Still captures and settled counts establish the displayed end states, not every
  frame during transition. The re-enabled immediate background count is `0` before
  settling at `1`; the final immediate active count is `1` before settling at `0`.
  These records alone do not demonstrate a visible leak or a race, nor prove their
  absence. The supplied narrative attributes this to diagnostic observer order.
- After the final re-enabled return, the log settles at `coverCount=0`; this batch
  has no separate screenshot of that final foreground state. The earlier resumed
  screenshot independently shows the first enabled foreground restoration.
- This is one synthetic harness run on one Simulator OS/device profile. It does
  not directly show Photos/Auth/Locker screens, physical hardware or every
  supported iOS version. No Figma or product design comparison was performed.
- The native narrative records another task briefly changing the Simulator window
  between disabled background entry and capture. The disabled screenshot visibly
  belongs to Screen Cover Probe and shows the expected disabled fixture; the
  observer did not independently control or verify device selection.

Suggested next decision: compare the migrated screenshots and native settled
counts with these same states. No adjacent task is proposed from this batch.

## SwiftPM and retained CocoaPods batches — 22 September 2026

Reviewed all six SwiftPM and all three retained CocoaPods screenshots, with their
native narratives and lifecycle logs. No visible screen-cover mismatch against
the baseline or new adjacent finding. This is a synthetic harness behavior
comparison; no product design or Figma comparison was performed.

Build/run identities from the supplied narratives: SwiftPM bundle
`io.ente.pilot.spmp.screenCoverProbe` (switcher label `Q002 SwiftPM`) and rebuilt
CocoaPods bundle `io.ente.pilot.screenCoverProbe` (label `Screen Cover Probe`), both
using the implementation worktree's relocated source on the same Q002 iPhone 17 /
iOS 26.5 Simulator. The narratives report unchanged native source bytes and the
same legacy lifecycle. Expectation sources remain PRD A3/A4 and the baseline above.

| Build and captured state | Observed comparison | Evidence |
| --- | --- | --- |
| SwiftPM enabled foreground | Fixture and enabled status readable, matching baseline. | [Foreground](evidence/swiftpm-enabled-foreground.png) |
| SwiftPM enabled switcher | Target card obscured; fixture text and controls unreadable, matching baseline. | [Enabled switcher](evidence/swiftpm-enabled-switcher.png) |
| SwiftPM first return | Readable enabled fixture restored, matching baseline. | [Resumed](evidence/swiftpm-resumed.png) |
| SwiftPM disabled switcher | Fixture readable and status disabled, matching baseline. | [Disabled switcher](evidence/swiftpm-disabled-switcher.png) |
| SwiftPM re-enabled switcher | Target card obscured again, matching baseline. | [Re-enabled switcher](evidence/swiftpm-reenabled-switcher.png) |
| SwiftPM final return after re-enable | Readable fixture and enabled status restored. This batch includes the final foreground capture absent from the baseline batch. | [Re-enabled resumed](evidence/swiftpm-reenabled-resumed.png) |
| Retained CocoaPods enabled foreground | Fixture and enabled status readable, matching baseline. | [Foreground](evidence/retained-pods-foreground.png) |
| Retained CocoaPods enabled switcher | Target card obscured; fixture text and controls unreadable, matching baseline. | [Switcher](evidence/retained-pods-switcher.png) |
| Retained CocoaPods return | Readable enabled fixture restored, matching baseline. | [Resumed](evidence/retained-pods-resumed.png) |

[SwiftPM lifecycle records](evidence/swiftpm-lifecycle.jsonl) corroborate settled
background counts `1, 0, 1` and settled active counts `0, 0, 0` for the narrated
enable/disable/re-enable journey. The final re-enable return settles at zero and
now also has direct screenshot evidence of readable foreground content.

The [retained CocoaPods log](evidence/retained-pods-lifecycle.jsonl) is cumulative.
Only the final `ready` block starting at `1790050106.0379529` belongs to the rebuilt
run according to [retained-pods-native.md](evidence/retained-pods-native.md). That
block has ready count `0`, settled background count `1`, and settled active count
`0`, agreeing with its three screenshots. Earlier disable/re-enable entries are
baseline evidence and are not counted as repeated testing of the rebuilt pod.

Remaining evidence limits:

- The observed parity covers saved end states in these synthetic harness runs on
  one Simulator OS/device profile. It does not directly validate Photos/Auth/Locker
  UI, physical devices, extensions or the oldest supported deployment versions.
- Neither batch supplies transition video or frame-by-frame capture. SwiftPM's
  re-enabled immediate background count `0` becomes settled `1`, and its final
  immediate active count `1` becomes settled `0`, as in the baseline. The saved
  evidence shows correct settled states but cannot settle transient exposure or
  system-alert/no-key-window behavior.
- The retained CocoaPods rerun covers initial double enable, background and return.
  It does not repeat disable/re-enable after rebuilding. SwiftPM does repeat those
  steps; the baseline covers the prior CocoaPods behavior.
- Native linking, absence of fallback, exact source hashes and publication-tree
  freshness are separate build/source evidence. This observer read the narratives
  but did not independently inspect build receipts, package graph, binaries or Git.
  Final acceptance remains with the parent.

Suggested next decision: use this comparison alongside the parent's build/source
checks. No follow-up task or implementation change is proposed by this observation.
