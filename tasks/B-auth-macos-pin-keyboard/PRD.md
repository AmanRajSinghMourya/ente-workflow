# Auth macOS PIN keyboard investigation

Task: Q001
Chat: codex://threads/01a0c780-9d6a-7a82-9dab-d92990604dc2
Checkout: /Users/amanraj/development/ente (this Mac)
Scope: Read-only investigation; no implementation requested or authorized.

## Report
Auth 4.4.25+1072 stopped accepting PIN keyboard input after an Intel-to-Apple-Silicon migration. Clicking the on-screen keypad works. Windows keyboard input works.

## Verified evidence
- Local auth-v4.4.25 tag bfd84e1de9469b4bf64b81fda615cfe92af5c3db has version 4.4.25+1072.
- lock_screen_pin.dart classifies Linux, macOS and Windows as desktop, enables native keyboard, and hides CustomPinKeypad. iOS takes the opposite branch.
- Both auth-v4.4.24 and auth-v4.4.25 retain the same platform predicate, native keyboard setting, autofocus:true and Pinput 5.0.2 dependency. The release refactors/styles PIN UI but does not remove desktop keyboard support.
- Cached Pinput 5.0.2 source disables focus requests and sets readOnly when useNativeKeyboard is false.
- Apple listing labels Auth Designed for iPad and requires Apple M1 or later for Mac: https://apps.apple.com/us/app/ente-auth-2fa-authenticator/id6444121398?platform=mac
- Official desktop installation instructions point to GitHub: https://ente.com/help/auth/faq/installing

## Conclusion and remaining check
Leading explanation is installation of the iOS/iPadOS App Store build on the new Apple Silicon Mac. It explains both the custom keypad and rejected typing. This is an inference, not confirmed installation provenance or an on-device reproduction. Ask whether downloaded from Mac App Store or desktop DMG and whether the listing says Designed for iPad. If desktop DMG is confirmed, investigate the actual running bundle and focus behavior. No claim that all macOS regressions are excluded.

## Validation
Read-only release comparison and dependency-source inspection; no product edits, builds, device interaction or tests. Spark evidence delegation was attempted but unavailable on this account.
