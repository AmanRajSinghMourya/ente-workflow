# Screen cover SwiftPM

SwiftPM packaging is implemented and committed locally. Native simulator checks
confirm that background privacy covers still appear and disappear as expected;
CocoaPods also works. Publication is waiting for the shared approval to update
the fork's main branch. I recommend completing that update so the PR contains
only this change, then publishing it and finishing the Claude and Codex bot reviews.

[Codex chat](codex://threads/01a0c739-e967-7e10-b51f-441b1226063f) ·
[Claude review](reviews/claude-design.md) ·
[Codex review](reviews/codex-local-review.md)

No PR has been opened yet.

> [!info]- Technical details and preserved history
> # Q002 · ente_screen_cover SwiftPM
> 
> [Task](codex://threads/01a0c739-e967-7e10-b51f-441b1226063f). **Status: needs decision — shared fork-main approval pending.**
> 
> Implementation, local validation and independent Codex review are complete. Commit
> `3356059deb6318388d65662fdf53d1244b70fc3b` is local; no push or PR yet.
> The coordinator already requested the shared fork-main fast-forward approval.
> Q002 must not sync fork main independently. After that approval/update, publish
> the ready fork PR, resume the same Claude session, and inspect actual Codex bot feedback.
> 
> ## Ownership and authorization
> 
> Host local; project local-a0f48e7f2a6d317290c1ab9e6791ed49.
> Primary `/Users/aman/Development/ente-2` remains clean on `aman/locker-sync-fix`
> at `6393d8561a77e34654b16a8f9d0598cce6bb4557`.
> Owned worktree `/Users/aman/Development/ente-2/.worktrees/I-mobile-ente-screen-cover-swiftpm`;
> branch `aman/mobile-ente-screen-cover-swiftpm`; base `719fbdd58d6e288ee6b52147898358eef10656d3`.
> `.task` resolves to this durable records directory and is locally excluded.
> The opening task relays Aman's 22 September five-package authorization for routine
> implementation, commits and ready PRs to AmanRajSinghMourya/ente:main. See the frozen
> [PRD](PRD.md) and [coordinator](codex://threads/01a0c6ea-8e55-7c00-8798-52d124669141).
> No additional product choice arose in Q002.
> 
> Actual model/effort verified by coordinator: gpt-6-astra/xhigh; danger-full-access,
> approval never. Fast configured off/default, per-request service tier not recorded.
> Spark inventory failed because its model is unsupported by this ChatGPT account;
> the primary performed the inventory. No security/configuration setting changed.
> 
> ## Final implementation
> 
> Six files, 26 additions and four deletions; Swift source relocation is 100% identical.
> A 22-line SwiftPM manifest exposes ente-screen-cover/ente_screen_cover, retains iOS13
> and follows the installed FlutterFramework dependency layout. CocoaPods selects the
> same source. One canonical checksum changes in each Photos/Auth/Locker Podfile.lock.
> No Dart API, native lifecycle, deployment floor, dependency version or global/app
> SwiftPM/UIScene guard changes.
> 
> Reviewed patch SHA256: `948f772f8f5ff9aa0537714fb65bb53cf7d971a1cd401a29138a40c03f23abaf`.
> PRD SHA256: `5a578edb0842cb6058222d27384e9ca8d476de7e89e074a29335e87f45adaa56`.
> Precommit source fingerprint: `890d430c2b7fade76d55ea5aa08fb8257a3828afa1e7f99bf25c93f35c178dce`.
> All 17 final receipts were verified against that source and original log hashes;
> [evidence/commit-tree-verification.json](evidence/commit-tree-verification.json)
> proves every reviewed blob and the staged tree equal the committed tree. Worktree clean.
> 
> ## Verification
> 
> - Baseline CocoaPods, SwiftPM-only and rebuilt retained CocoaPods native builds/run
>   passed using the real package path and legacy app lifecycle. SwiftPM graph and
>   registrant verified; no Pods directory in the SwiftPM harness.
> - Dedicated iPhone17/iOS26.5 simulator C9F0AAB3-EE28-4D0E-81B6-A3F471ED8878:
>   enabled/re-enabled background cover blurred, disabled background readable,
>   foreground cover removed. SwiftPM background counts [1,0,1], foreground [0,0,0].
> - Unsigned arm64 iOS Release SwiftPM build passed; binary contains plugin symbols.
> - All three app `pod install --deployment` checks passed. Frozen 44 pubspecs,
>   enforced lockfile, formatting, source plurals, FRB codegen and full mobile analysis passed.
> - Workspace tests: 20 packages, 788 passed, one skipped, no failed package.
>   Includes Auth53, Locker21, Photos547 and lock_screen18.
> 
> Evidence: [baseline](evidence/baseline-native.md), [SwiftPM](evidence/swiftpm-native.md),
> [retained Pods](evidence/retained-pods-native.md),
> [test summary](evidence/workspace-test-summary.json),
> [receipt verification](evidence/precommit-receipt-verification.json).
> Native evidence observer found no mismatch; limitations in [followups](followups.md).
> This is harness/simulator behavior plus unsigned device compilation, not physical-device
> runtime or full-app end-to-end proof. No Rust clippy or completed hosted-CI claim.
> 
> Initial failing receipts are preserved: expected missing manifest before implementation;
> wrong direct-Ruby checksum corrected using actual CocoaPods JSON checksum d9be2699...;
> CLT27/Xcode26.6 mismatch resolved with command-scoped Xcode SDKROOT; initial analyzer
> asset warnings resolved by initializing only CI-pinned simple-icons submodule.
> No unrelated source fix was needed. Full source and Dart lockfiles stayed unchanged
> through codegen/dependency resolution.
> 
> ## Reviews
> 
> Claude design review completed in real persistent session
> `aeed0c77-96e5-487b-ae51-d7a704dd106e`; session file and returned ID verified.
> [Review](reviews/claude-design.md). Manifest layout, iOS13 floor, checksum refresh
> and legacy lifecycle accepted. External-workspace dependency concern disproved by
> actual path-dependency builds. Nil-window/system-overlay timing is existing behavior
> outside this packaging slice; native proof limitations retained.
> 
> Independent read-only Codex CLI review gpt-6-astra/xhigh, session
> `01a0c751-91a6-74b2-af4f-0618a140e808`: no actionable findings.
> [Review](reviews/codex-local-review.md). Its stale-resolution-receipt note was resolved
> by `frozen-resolution-final`; all final receipts verified before commit.
> 
> Required post-PR Claude code review and actual Codex bot review are still pending.
> Resume **the exact Claude design session above** using `--resume`, from original
> primary cwd with worktree/records read access. No new session, no `/code-review`.
> 
> ## Publication handoff
> 
> [publication.json](publication.json) records the exact authorized identity/title/body.
> Head and target: AmanRajSinghMourya/ente; base main; account aman-pilot;
> remote aman-review, push URL git@github-aman-pilot:AmanRajSinghMourya/ente.git.
> Commit identity AmanRajSinghMourya <amanrajmourya7@gmail.com>.
> Title `[mobile] Add SwiftPM support for screen cover`; empty body; ready, not draft.
> 
> After coordinator verifies the approved fork-main fast-forward, refresh live
> base/account/remote and ensure the PR range contains only this task. Push the exact
> branch normally, create through gh, attach PR and fire one confetti burst. Register
> PR identity, resume Claude, inspect actual Codex feedback, and record dispositions.
> Do not activate held review-learning/cleanup jobs. GUI released; dedicated device
> retained for follow-up. Earlier working notes retained in evidence/board-before-commit-summary.md.
