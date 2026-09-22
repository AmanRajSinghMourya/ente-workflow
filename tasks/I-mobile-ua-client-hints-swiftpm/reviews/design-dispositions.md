# Design dispositions

Claude session88ff3e69-6f04-43a9-9a56-fc33380e64ff completed normally; raw JSON and wrapper receipt preserved in evidence/claude-design.json*. Review source read only and persistent session verified.

1. Harness scope ambiguity: clarified explicitly in acceptance. Original plan already specified separate harness and excluded app guard changes. No product blocker.
2. CI/native proof distinction: clarified. Native results are separate local evidence; CI-only checks were never treated as runtime proof.
3. Baseline mismatch: primary checkout ef563ca is intentionally untouched; source snapshots use recorded origin/main08d1056. They represent distinct facts, not a falsely reviewed HEAD. Fetch and record actual worktree base after review as planned.
4. Six-file scope and pod version: accepted. CocoaPods1.17.0 verified. Six is estimate; file-contract gate will reject unexpected churn for inspection.
5. Resource manager paths: accepted and already implemented: Pods ua_client_hints_privacy versus SwiftPM ua_client_hints_ua_client_hints; both match archive plist content.
6. Full Photos end-to-end build suggestion: outside minimum harness proof; byte-identical native/Dart code and real runtime package outputs cover package upgrade behavior. App dependency/pod resolution, analysis and affected tests remain required. No full app runtime claim unless performed.

Native hypothesis resolved experimentally:1.4.1 CocoaPods baseline,1.5.0 CocoaPods and fresh1.5.0 SwiftPM harness builds/runs passed with identical raw metadata, userAgent and all headers. Typed metadata asserted. SwiftPM harness has no Podfile/Podfile.lock and its generated package/registrant include ua-client-hints/UAClientHintsPlugin. Both bundle privacy resources validated. No source/cache patches or global flag changes.
