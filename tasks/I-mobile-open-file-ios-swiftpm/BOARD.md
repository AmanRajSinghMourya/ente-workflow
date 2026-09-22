# Locker file opening: SwiftPM readiness

Locker’s dependency update is committed locally. Native file-opening checks and all 20 mobile test suites passed; independent Codex review found no bugs. This prepares the plugin for SwiftPM while preserving current behavior. Publication awaits the coordinator’s requested approval to update the shared fork’s main branch. Recommendation: approve that shared update, then publish and complete the required Claude and GitHub bot reviews.

- [Codex chat](codex://threads/01a0c73b-4733-76a3-a6c5-655aa04909d4)
- PR: not opened; shared publication blocker remains.
- [Claude review](reviews/design.md) — saved design review.

> [!info]- Technical details and preserved history
> # Q003 board
> 
> Chat: [Q003](codex://threads/01a0c73b-4733-76a3-a6c5-655aa04909d4). Assignment: local / local-ac1dc9d855099b51090b99fd92b5a561 / /Users/aman/Development/ente.
> Status: locally committed and ready for review; publication blocked on coordinator-owned shared fork-main approval. No push/PR yet.
> Authorization: explicit batch scope in opening message; routine plan/implementation/commit/fork PR permitted. No product/security/OS/lifecycle choices authorized.
> Settings verified in own turn_context: gpt-6-astra, xhigh, never, danger-full-access. service_tier is absent; coordinator verified default. Spark attempt failed: gpt-5.3-codex-spark unsupported with ChatGPT account; primary performs evidence work.
> Primary starting HEAD ef563ca9194a7c74336a331771cbb193ae52e466, clean main; origin/main inspection 08d10562021967292c7b106d369fcf41d0f30bce.
> Planned worktree: /Users/aman/Development/ente/.worktrees/I-mobile-open-file-ios-swiftpm; planned branch aman/mobile-open-file-ios-swiftpm.
> Claude persistent session reserved for design: 943f8f50-f1bc-4bea-86b8-9c634395dd71. Actual completion/session persistence pending.
> Evidence: evidence/source-inspection.txt; evidence/source-snapshot from inspected origin/main; verified archives extracted under evidence/open_file_ios-*; fresh pub/GitHub advisory JSON.
> Simulator: none booted at inventory. Claim an available simulator in pilot BOARD before native use.
> PR/review SHA: none. Native evidence: not yet run. Next: Claude design review, then fetch latest main and create isolated worktree.
> 
> Baseline layout check failed for the intended missing Flutter manifest; candidate layout check passed. Logs/receipts layout-baseline.json and layout-candidate.json. Runtime source byte equality confirmed in runtime-source-hashes.txt. Native probe source/contract prepared; not executed. Dedicated simulator 38C73E90-17C6-4862-B92B-46770B6E07C7 claimed in pilot BOARD.
> 
> Claude design review complete; actual persistent session verified 943f8f50-f1bc-4bea-86b8-9c634395dd71. Full output reviews/design.md; independent dispositions reviews/design-dispositions.md. Technical approach accepted with precise readiness wording; no routine permission needed under batch authorization.
> 
> Fetched main; worktree created at /Users/aman/Development/ente/.worktrees/I-mobile-open-file-ios-swiftpm, branch aman/mobile-open-file-ios-swiftpm, immutable base 719fbdd58d6e288ee6b52147898358eef10656d3. Fresh-main delta is unrelated scanner/CI/web work; relevant dependency/native paths unchanged. .task directory symlink and local exclusion verified. Implementation authorized by batch; native validation first.
> 
> ## Native package evidence
> 
> Native baseline1.0.4 and candidate1.1.0 builds passed on Flutter3.47.2/Xcode26.6. Both exact Locker AppDelegate copies, no UIApplicationSceneManifest, migration disabled. Baseline includes open_file_ios Pod; candidate has generated SwiftPM open-file-ios product and no Podfile.lock; linked OpenFilePlugin class present. See native-build-proof.txt and full build logs/receipts. Harness hashes are recorded separately because source receipt fingerprints cover worktree, not external harness.
> On dedicated iPhone17/iOS26.5 38C73E90-17C6-4862-B92B-46770B6E07C7, baseline and candidate both returned fileNotFound, rendered named text with intact original contents in QuickLook, and returned done after dismiss. Saved UI JSON/screenshots and run logs under evidence. This resolves the suspected legacy lifecycle risk for plugin; full Locker app proof still pending. No product lifecycle changes.
> 
> ## Implementation/checks
> 
> Upgraded with flutter pub upgrade open_file_ios after dry-run selected one dependency. Dry-run's Flutter postprocessing complained missing package_config; baseline enforce-lockfile pub get then passed. Actual upgrade changed only ios platform version/hash and generated SDK floor >=3.11.0-0 to >=3.11.0. No other package moved. pod install using CocoaPods1.17.0 changed only open_file_ios checksum. Frozen-pubspecs passed. Initial Locker file test failed on missing generated Rust bindings; not a product regression. CI cargo codegen initially failed host link because default SDK search found CLT27 with Xcode26 linker; command-local SDKROOT=Xcode MacOSX26.5 fixes host compilation (generation pending).
> 
> Fork base coordination: parent reported target main202commits behind upstream and requested shared fast-forward approval. Do not independently sync or publish a PR with unrelated history; check pilot BOARD before publication.
> 
> ## Locker native handoff verified
> 
> Actual Locker Runner simulator build succeeded (Flutter command exit0,300.5s Xcode build). A test-only external Dart entrypoint initializes native Configuration and calls unchanged FileUtil.openFile(context, file) on a real cached EnteFile. No mocked file channel or product/native source edits. On dedicated iPhone17/iOS26.5, QuickLook rendered Locker Q003 original with exact fixture text; dismissal returned and verified actual open_handoff copy bytes against cached source. A complete repeated flow passed. Screenshot/accessibility/action evidence: locker-valid-handoff.png, locker-returned.png, maestro-locker-handoff.json, maestro-locker-completion.json. First ID-based Done tap did not dismiss; the observed text selector Done succeeded, then full flow with animation wait passed. Not classified as product regression from one automation miss.
> 
> Build wrapper receipt marked fail solely because Flutter removed MinimumOSVersion from tracked AppFrameworkInfo.plist during build; command itself succeeded. Exact known generated removal was restored afterward. Photos CI codegen temporarily removed/recreated four tracked generated model files and ended with those files unchanged. Product diff remains exactly two lockfiles/8changed lines. Real native source/entrypoint/binary hashes in locker-native-proof.json. This is a representative real Locker cached-file handoff, not a logged-in remote download/account journey or signed device archive.
> 
> ## Final validation milestone
> 
> Full mobile workspace tests, Flutter analysis, 1923-file formatting and Rust clippy for both Photos/Locker FRB packages passed with final source fingerprint330e9ce91f5e56c3035cd175e06d7beff4f893450781b34951e95415f2eff334. Locked pub resolution, frozen pubspecs and all three CocoaPods deployment checks share that fingerprint. Command-local Xcode SDKROOT fixed only host codegen/link prerequisites. Final native evidence freshness check passed. Source ARB/auth icon checks are refreshed after the temporary generated plist drift. See evidence/validation-summary.md.
> 
> ## Reviewed commit and continuation
> 
> Local commit02aab68dd894690ce934a206fffd456f5acba151, tree66b0f4e259eb37fc401b05410e64c6c6c3aab972. Author AmanRajSinghMourya <amanrajmourya7@gmail.com>. Working tree clean. Exact base-to-HEAD binary patch equals the tested/reviewed patch330e9ce91f5e56c3035cd175e06d7beff4f893450781b34951e95415f2eff334. See evidence/committed-tree.json; old check receipts are precommit HEAD and are connected to committed source by exact tree/patch identity, not relabeled. PRD digest remains41802f6278f4b154fa7f386828135ce54b89c08474004b67302ad1614b00f2d5.
> 
> Independent Codex CLI gpt-6-astra/xhigh read-only review completed with no confirmed bugs; all acceptance areas checked, full output/dispositions in reviews. Repository-wide .github/checks/run.sh additionally passed after installing its existing pinned Prettier3.8.3 tool with scripts disabled (official metadata/integrity and GitHub/npm advisory checks retained). Local Node25.9.0 differs from CI24. Exact unchanged product patch. Hosted CI and GitHub dependency-review remain pending PR.
> 
> Publication remains blocked only by shared fork main202behind. No independent main sync, branch push or PR performed. Coordinator owns approval/sync. After coordinator verifies approved fast-forward, recheck live base/account/destination and publish exact ready PR in publication.json; attach and fire one confetti. Then extensively review through claude --resume943f8f50-f1bc-4bea-86b8-9c634395dd71 in safe read-only mode, preserving inputs/head, and inspect actual GitHub Codex bot feedback on that head. No fresh Claude session, unrelated PR history or substituted local review. Review-learning/cleanup holds stay unchanged.
