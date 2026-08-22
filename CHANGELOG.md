# Changelog

## Unreleased

### Added
- **`DM_VERIFICATION_COMPLETED_MESSAGE` toggle.** Sends the verification completed message to the member's DMs as well. It is independent of `SEND_VERIFICATION_COMPLETED_MESSAGE`, so disabling that one and enabling this gives a DM-only welcome. Off by default, and members with closed DMs are skipped silently. Available on the web dashboard under Module Toggles.
- **`VERIFICATION_BUTTON_LABEL` 💎 premium setting.** Lets a server change the text on the verification button (`/config messages key:verification_button_label`, or the Messages page on the dashboard). Unset, non-premium, or blank values keep the current `Start Age Verification!` label; values are capped at Discord's 80 character button limit.

## 2026-07-10

### Added
- **Cross-server ID awareness.** AgeVerifier now notifies your servers when an ID check is created for a member in another server, and when a member successfully ID-verifies in another server (new `classes/verification/inform.py`).
- **`AUTOKICK_ON_DISCREPANCY` toggle.** Automatically kicks a member when the age they enter doesn't match the date of birth they provided during verification, with an appeal message.
- **`/whitelist apply` requirements.** The application command now runs automated eligibility checks: active premium, 100+ members, 6+ months old, server-wide 2FA required, and Community server enabled.

### Changed
- **Whitelisting requirements overhauled.** Split into automatic checks (run on apply) and manual review, and removed the one-time $5 service fee.
- **Versioning bump.**
- **Docs generator (`docsGenerator.py`)** now skips background event listeners and developer/owner-only commands, and no longer leaks the internal discord.py Cog base docstring into the public command pages.
- **Improved cog/command docstrings** for the General cog, the Surveys leave-survey listener, and the developer `cache` command.

### Fixed
- **IDSubmit button** fixes and related verification-transaction handling.

### Documentation
- **New pages:** Getting Started, Verifying Your Age (member-facing), Verification Methods, Web Dashboard, Premium, FAQ & Troubleshooting, Permissions Guide, and an in-depth Configuration Guide.
- **Premium/free reconciliation** across the config guide to match the dashboard (Reverify log channel, reverification roles, automated lobby cleanup & kicking, leave message, and survey are premium).
- **Navigation cleanup:** renumbered all doc pages into a single consistent order with no collisions.
- **Homepage updates:** corrected the dashboard link (strykerdevelopment.com), added the support-server link and a Getting Started pointer.
- Regenerated/cleaned the affected auto-generated command pages (Config, General, Surveys) to drop dev-only/legacy entries and background events.
