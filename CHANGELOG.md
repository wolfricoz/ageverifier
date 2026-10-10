# Changelog

## Unreleased

### Added
- **`DM_VERIFICATION_COMPLETED_MESSAGE` toggle.** Sends the verification completed message to the member's DMs as well. It is independent of `SEND_VERIFICATION_COMPLETED_MESSAGE`, so disabling that one and enabling this gives a DM-only welcome. Off by default, and members with closed DMs are skipped silently. Available on the web dashboard under Module Toggles.
- **`VERIFICATION_BUTTON_LABEL` 💎 premium setting.** Lets a server change the text on the verification button (`/config messages key:verification_button_label`, or the Messages page on the dashboard). Unset, non-premium, or blank values keep the current `Start Age Verification!` label; values are capped at Discord's 80 character button limit.
- **Alt detection by IP and device.** Website verifications now list **Potential Alts** on the approval card: other accounts that verified from the same IP address or the same browser and device in the last 30 days, each labelled `IP`, `device` or `IP + device`. Addresses and device fingerprints are stored as keyed one-way hashes and cleared after 30 days (`classes/alts.py`).
- **Risk score.** Website verifications (date of birth and ID) show one **Risk Score** out of 100 on the approval card, built from VPN/proxy use, the strongest alt match and Discord account age, with the reasons listed and a Low/Medium/High band. On by default; hide it with the new `risk_score` option of `/config approval_toggles` (`classes/verification/risk.py`).
- **Abandoned verification reminder 💎 premium.** `/config verification_reminder minutes:<n>` DMs members their verification link once when they opened the website verification page but didn't finish within `n` minutes (up to 7 days, `0` turns it off). Members who left or were verified another way are skipped. The dashboard reports page opens through the new `POST /age/opened/{guild_id}/{user_id}` endpoint.
- **Support module.** `/support help`, `feedback`, `bug`, `report`, `suggest` and `info` open a ticket in the support server; staff replies are sent back to the member by DM.
- **Withdraw consent on ID submissions.** New ID submissions get a *Withdraw consent and delete my ID* button that deletes the image straight away and closes the staff review. It doesn't clear an ID check staff placed on the member.

### Changed
- **Website verification is free.** It no longer needs premium, and it stays the default for new servers.
- **ID images are deleted after 7 days.** An hourly task now deletes ID images that are older than 7 days and closes their staff review, so an ID that was never reviewed no longer stays in the member's DMs.
- **Docs generator** also skips commands behind DevTools' `@check_access()` developer check (such as `/dev stats_report`), not only `@commands.is_owner()` ones.
- **Internal:** a weekly developer stats report posts on Sundays (`/dev stats_report` posts it on demand), and the RMRbot approvals and advertisements tables moved into this repo's migrations.

### Fixed
- **Website verification link reuse.** Pressing the verify button again now hands back the member's unfinished link instead of creating a new one every time.
- **Website verification link ownership.** Submitting a verification checks that the link belongs to the submitting member, so one member's link can't be marked complete by another account.
- **Approval ping role check** failed to resolve the role and reported "Unable to retrieve role" for a role that exists.
- **Sentry errors** in config channel lookups (deleted channels retried until the queue timeout), invite logging, lobby flows, `dob_to_age` with `-` and `.` separators, the ID submit button timing out, already-deleted messages and permission notices.

### Privacy
- **Dates of birth are kept out of the logs.** `dob` options are redacted in the slash-command log, which is also sent to Sentry.
- **Members waiting on a GDPR removal** no longer show up as IP or device alts during the 30 day grace period.

### Documentation
- **Privacy policy** covers the 4.0 online verification data: device fingerprints, VPN and proxy checks, verification page progress, website request and security logs, how ID images are handled during review, and the withdraw button.
- **Configuration Guide:** the Verification Reminder, the Risk Score approval option, and a staff guide to reading the Risk Score and Potential Alts fields. **Verification Methods** describes them under Website verification.
- Regenerated the Config command page with `verification_reminder`.

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
