# Design review dispositions

Session 943f8f50-f1bc-4bea-86b8-9c634395dd71 persisted and completed with actual JSON output in evidence/claude-design.json.log (Opus5; Haiku used by CLI auxiliary operation). Review made no repo changes.

- F1: accept clearer readiness wording and commit subject. Guards were already explicitly excluded in PRD; its assertion that they were never mentioned is overstated. PRD now directly states CocoaPods remains active. Routine wording covered by batch authority.
- F2/F4: accept minimum transitive-only upgrade and FlutterFramework design; must still prove build.
- F3: accept broken discovery. Reject exact claim that 1.0.4 manifest declares path Sources/open_file_ios: actual file has no path field. Its default source lookup is unsuitable at the nested root. Do not repeat invented quotation.
- F5: accept required checksum update and tight Podfile diff. CocoaPods checksum uses normalized spec serialization, not simply raw file SHA1; let CocoaPods generate it. Recheck fresh main rather than old primary Podfile.lock.
- F6: accept SDK/OS compatibility. Reject new workspace Dart-floor concern: existing origin/main lock already declares Dart>=3.11.0-0 and Flutter>=3.44.0. Do not change root SDK or add misleading PR warning.
- F7: agree native source is unchanged, so legacy issue would be pre-existing. Do not weaken user-required native acceptance based on expected implicit scenes. Verify real runtime.
- F8: accept separate harness SwiftPM evidence and Locker CocoaPods regression evidence. Harness pins platform version explicitly to compare baseline/candidate. Runtime source hashes independently verified.
- Future app archive integration belongs to the already-planned integration checkpoint; no guard/CI changes in this task.

No product decision needed to conduct the agreed migration and validation. Native failure, if any, remains publication blocker.
