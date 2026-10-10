---
layout: default
title: Privacy Policy
nav_order: 13
---

<h1 style="text-align: center">Privacy Policy</h1>

_Last Updated: 10/10/2026_

# Introduction
This privacy policy outlines how AgeVerifier ("we," "our," or "us") collects, uses, and protects your (the end user) personal data when you interact with the AgeVerifier bot. By using AgeVerifier, you agree to the terms and conditions of this policy.

References in this document may refer to servers as guilds, as that is the terminology used within Discord's API.

## Why do we store your data?
To verify users, we collect the following personal data:

- **Date of birth:** Used to calculate the age and to verify future verification attempts.
- **Age:** This data is collected but not stored; it is collected from the user only to validate that the age matches the date of birth submitted.
- **Discord ID:** While not technically personal data, we collect and store users’ Discord ID and combine it with the submitted Date of Birth.
- **IP address:** Collected only when a user verifies through our website, and never stored in readable form. See *IP Addresses* below.
- **Device fingerprint:** Collected only when a user verifies through our website, and never stored in readable form. See *Device Fingerprints* below.
- **VPN and proxy check result:** Calculated when a user verifies through our website. See *VPN and Proxy Checks* below.
- **Verification page progress:** When a user opens and completes our website's verification page. See *Verification Page Progress* below.

The combination of age and date of birth is used as a simple method of verifying the age of users. By storing the date of birth with Discord ID, we can ensure that users give the same date of birth in future interactions or flag them for a discrepancy.

None of the website data described below is collected when verifying directly through Discord rather than through our website.

### IP Addresses
When a user completes verification through our website, we record the IP address that the verification was submitted from. This is used to identify users attempting to circumvent age verification by creating additional accounts, which protects the integrity of the verification system and the member guilds relying on it.

We do not store the IP address in our verification database. Before anything is written to it, the address is converted into a set of one-way cryptographic hashes using a secret key held only by AgeVerifier. We store those hashes and nothing else. Alongside the exact address, we also hash the surrounding network ranges, which allows us to recognise verifications originating from the same internet connection or the same internet provider even after a provider has reassigned a user's address.

Our website, which is separate from the verification database, keeps two logs that contain IP addresses in readable form:

- **Request log:** every page request to the website is recorded with the IP address, browser type (user agent), the page requested and, if logged in, the Discord ID, to keep the website secure and diagnose errors. Dates of birth and ages are removed before anything is recorded. These records are permanently erased after **30 days**.
- **Security log:** when the VPN and proxy check (below) flags a verification attempt, the website records the attempt, including the IP address and the result of the check, so that we can investigate abuse of the verification system. These entries are permanently erased after **14 days**.

IP data is never used to track a user's physical location. The only location lookup we make is part of the VPN and proxy check described below, and its result is not stored.

### Device Fingerprints
When a user verifies through our website, the verification page calculates a device fingerprint: a value derived from technical characteristics of the browser and device, so that verifications from the same device can be recognised. It is used for the same purpose as the IP address: identifying users who create additional accounts to circumvent age verification, including users who change their IP address or switch to mobile data to avoid an IP match.

The fingerprint is calculated from the following characteristics, and from nothing else:

- How the browser draws a short piece of text and graphics (which differs by graphics card, driver and font rendering).
- The graphics card vendor and model reported by the browser.
- Screen resolution, colour depth and pixel ratio.
- The browser's time zone and language settings.
- The platform, number of processor cores, approximate device memory and touch support reported by the browser.

These characteristics are combined and converted into a one-way hash inside the user's browser, so only the hash ever leaves the device; the characteristics themselves are never sent to us. When the hash reaches AgeVerifier, it is hashed again with the same secret key used for IP addresses before it is stored. The fingerprint does not use cookies and does not contain the user's IP address, name, or any account information.

Different devices of the same model, running the same software, can produce the same fingerprint. For this reason a fingerprint match is treated as a weaker signal than an IP match, and it is only ever shown to guild staff as a possible match for them to review, never as proof.

### VPN and Proxy Checks
When a user verifies through our website, the website checks whether the connection comes from a VPN, a proxy, the Tor network, or a hosting provider rather than a home or mobile connection. To do this, the IP address is looked up in databases that are stored on our own server, so the address is not sent to any third party:

- Published lists of Tor exit nodes and VPN provider servers.
- The network operator (autonomous system) the address belongs to.
- A proxy detection database.
- The time zone of the address's approximate location, which is compared with the time zone reported by the user's browser. A mismatch only counts if one of the other checks already found something, because travellers and expatriates often have a mismatch on its own.

The result is a score from 0 to 100. Depending on the score, the website will either:

- **Allow** the verification normally;
- **Flag** it, in which case the verification goes ahead and the score is shown to the guild's staff on the approval message; or
- **Block** it, in which case the user is asked to turn off their VPN, proxy or Tor connection and try again.

The location and network details from these lookups are not stored. Only the score and whether the attempt was flagged are passed to AgeVerifier, and they are shown to guild staff (see *Automated Decision-Making*) rather than stored in our verification database.

### Verification Page Progress
When a user opens the verification page on our website, we record which guild and verification link it is for, the user's Discord ID, which steps of the page they reached, and when they opened, last used and completed it. This tells guilds where members drop out of the verification process, and it lets AgeVerifier send a one-time reminder by Discord direct message to members who opened the page but did not finish, if the guild has enabled that reminder.

## Legal Basis for Data Collection
We collect, store, and process user data under the lawful basis of **legitimate interest** (ensuring compliance with platform rules) and **user consent** when users interact with AgeVerifier.

## Discrepancies
In the event of an age discrepancy, we reserve the right to request additional information to confirm the user’s legal age. This process may involve:

- **Minor Discrepancies:** If the discrepancy appears to be a simple error (e.g., a typo), we may ask for clarification.
- **Significant Discrepancies:** In cases where the discrepancy is more substantial, moderation staff from an AgeVerifier member guild may request that legal documentation (e.g., government-issued ID) be provided to validate the user-submitted information.

In such cases, staff from that server will advise on what is required to resolve the discrepancy. Requirements may vary between member guilds depending on their individual rules and requirements, and they reserve the right to deny access to users who do not comply with these requirements. All other sensitive details in the verification artifact, such as name, address, and unrequested biometrics, should be masked out by the submitter for privacy.

For clarity, **AgeVerifier does not store the legal documentation provided in its database**. Only your date of birth and a conditional flag indicating that the user’s age has been verified via ID will be retained. This process ensures that user privacy is respected while maintaining the integrity of our age verification system.

### How ID Images Are Handled During Review
While an ID is waiting for review, the image is kept in one place only: a message from AgeVerifier in the user's own Discord direct messages, which serves as the user's private copy of what they submitted. IDs submitted through our website are first re-encoded to remove hidden data such as location and camera details, and our website does not keep a copy.

The image is not posted in the guild's channels. The guild's staff are shown a notice that an ID was submitted, and an administrator who opens it sees the image in a private Discord message that only they can see and that disappears when they close or restart Discord. Staff are instructed not to save or share submitted IDs.

The direct message holding the image is deleted when the review is completed, when the user submits a new ID, or after **7 days**, whichever comes first. After that, no copy is kept by AgeVerifier.

Users can withdraw their consent at any time before then with the **Withdraw consent and delete my ID** button on that message. This deletes the image immediately and cancels the review: the guild's staff are told the submission was withdrawn and can no longer open it. Withdrawing does not remove a requirement the guild has placed on the user to verify by ID; the user can submit again later if they still need to verify.

When an ID is submitted through Discord, the user sends the image to AgeVerifier in their direct messages. That original message belongs to the user, and Discord does not allow AgeVerifier to delete it, so we recommend deleting it yourself once AgeVerifier has confirmed it received your ID.

## Age Restrictions
AgeVerifier is designed for use by individuals aged 18 and above. Anyone under the age of 18 may not use our services. In cases where an individual under 18 submits their information, only the Discord ID and a conditional flag indicating that the user is underage will be retained in our system.

## How We Use Your Data
We use the user-submitted data collected for the following purposes:

- Verifying user eligibility based on date of birth.
- Ensuring compliance with platform, guild, or legal age requirements.
- Improving the accuracy and/or functionality of our age verification system.
- Assigning roles based on your age and guild requirements.
- Detecting attempts to bypass age verification through the use of additional accounts, VPNs or proxies.
- Reminding users who started verifying through our website but did not finish, where the guild has enabled this.
- Diagnosing problems in servers that remove AgeVerifier shortly after adding it (see *Diagnostic Logs*).

## Data Minimization
We only collect the minimum amount of data required for age verification and do not use user data for purposes other than those explicitly stated in this policy.

## Retention Policy and Data Lifecycles
To remain compliant with data minimization protocols, avoid unnecessary data storage, and respect user privacy, AgeVerifier enforces specific, time-bounded data lifecycles depending on the classification of the data recorded. These schedules are executed via automated database maintenance routines.

### Operational Tracking and Session Logs
Data generated from temporary interactions with the verification infrastructure is subject to a rolling execution window:
- **Website Session Data:** Relational web metadata logs are permanently erased after 90 days.
- **Lobby Configuration Data:** Interaction and queuing data used during active verification sessions are permanently erased after 90 days.
- **IP Address Hashes:** The hashed IP data described above is permanently erased **30 days** after the address was last seen. Because internet providers routinely reassign addresses, this data stops being meaningful well before the one-year profile retention period, and it is therefore erased on a much shorter schedule rather than being kept for the life of the verification record.
- **Website Request and Security Logs:** The website request log described under *IP Addresses* is permanently erased after **30 days**, and the website security log after **14 days**.
- **Device Fingerprint Hashes:** The hashed device fingerprint described above is permanently erased **30 days** after it was last recorded, on the same schedule as IP address hashes and for the same reason.
- **Verification Page Progress:** Records of a user's progress through our website's verification page are permanently erased after **180 days**. The verification link itself, including when it was opened and whether a reminder was sent, is erased after 90 days as part of the website session data above.
- **Diagnostic Logs:** AgeVerifier keeps technical log files of the commands it runs and the errors it encounters, which can include Discord usernames and IDs. When a guild removes AgeVerifier within 7 days of adding it, after using at least one command, the log entries that mention that guild are copied into a separate file so we can find out what went wrong. These files are permanently erased after **90 days**. Because they are stored per guild rather than per user, they are not removed by `/gdpr removal`; to have your details removed from them sooner, contact us as described under *How to Make These Requests?*.

### Historical Analytical Metrics
- **Join History Logs:** Relational records tracking user guild join histories are retained for analytical purposes but undergo **irreversible anonymization** after 90 days. During this process, individual user identification markers (`uid`) are unlinked and mapped permanently to a generic anonymous system identifier. This allows member guilds to preserve non-identifiable, aggregate server historical statistics without tracking individual user behavior over time.

### Core Verification Profiles
- **Inactivity Deletion:** User profile verification records (containing the linked Discord ID and Date of Birth) are completely and permanently erased from the active database after **one year of continuous absence or inactivity** across all member guilds utilizing AgeVerifier.

## Automated Decision-Making
AgeVerifier uses automated processes to flag discrepancies in submitted data (e.g., mismatched dates of birth). Flagged cases may require manual review by guild staff. Additionally, guilds can enable automated approvals for correct age and date of birth matches to reduce the strain on the guild's staff.

For verifications through our website, the approval message shown to guild staff can also include:

- **Potential alternate accounts:** other Discord accounts that previously verified from the same IP address, network or device fingerprint, and which of these they share.
- **A risk score:** a number from 0 to 100, with a low, medium or high rating, combining the VPN and proxy check, any potential alternate accounts, and the age of the Discord account. The reasons that contributed to the score are listed with it.

These are signals for guild staff to consider, not decisions: they do not deny anyone's verification on their own, and the final decision is made by the guild's staff. Guilds can turn the risk score off. The approval message is posted in the guild's own staff channel on Discord, so how long it remains there is controlled by that guild.

The one automated refusal is the VPN and proxy check: when it is confident that a connection is a VPN, proxy or Tor, the website will not accept the verification until the user connects without one. If you believe your connection was blocked by mistake, contact the guild's staff or our support guild.

## How We Store and Protect Your Data
User data is transmitted between Discord and the AgeVerifier bot over encrypted connections (TLS) and is stored in a database local to the AgeVerifier bot.

Dates of birth are encrypted at rest, and are decrypted only when needed to carry out the verification purposes described in this policy. IP addresses and device fingerprints are never written to the verification database in readable form; only the one-way hashes described above are stored, so the underlying values are not present in that database or in any backup of it.

## Retention Policy
User data is pruned from the database automatically after **one year of absence** on member guilds using AgeVerifier.

## Whitelisted Guilds and Data Access
Moderation teams from certain whitelisted guilds are granted access to specific data to assist in managing the AgeVerifier database. These guilds are carefully vetted and must adhere to the following guidelines:

### Access to Dates of Birth
- Whitelisted guilds may only view dates of birth to verify users' ages.

### Editing Dates of Birth
- Whitelisted guilds may only edit dates of birth in specific cases, such as correcting typos or resolving discrepancies in age verification.

### Restricted Access to Management
- Dates of birth are accessible only to the management team of the whitelisted guild.

### Accountability for Whitelisted Guilds
Management teams of whitelisted guilds are trained and regularly inspected by AgeVerifier to ensure compliance. If a guild fails to adhere to these guidelines, it will lose its whitelisted status.

## Rules Pertaining to Member Guilds
Non-whitelisted guilds do not have the ability to access stored dates of birth provided from other member servers and may not directly edit date of birth in any cases.

## Data Sharing
We do not share user personal data with third parties unless required by law or to comply with legal obligations. User personal data is strictly used for verification purposes within the AgeVerifier bot.

We will never sell, lease, or otherwise distribute user personal data to unauthorized third parties.

## User Rights
In accordance with the **General Data Protection Regulation (GDPR)**, users have the following rights regarding personal data:

### Access to User Data
- Users have the right to request a copy of the personal data we hold about them.

### Correction of Inaccurate Data
- If a user believes that any of the data we hold is incorrect or incomplete, the user can request corrections to ensure accuracy.

### Data Deletion
- Users have the right to request the deletion of that user’s personal data where applicable. Deleting a user's verification record also deletes the IP address hashes and device fingerprint hash stored with it.

## Processing of Requests
All requests will be responded to within **30 days** after submission in accordance with our retention policy and applicable legal obligations.

### How to Make These Requests?
To make a request, you can:

- Join our support guild.
- Send an email to **rico@strykerdevelopment.com**.
- Use the commands provided in a participating server running AgeVerifier:
  - `/gdpr removal`: Can be utilized to request the removal of that user’s data.
  - `/gdpr data`: Can be utilized to obtain a copy of the personal data we hold about the user.

For corrections of inaccurate data, please join our support guild and open a ticket for assistance.

**Note:** Excessive or unreasonable requests may incur a fee or be ignored, in accordance with GDPR regulations.

## Data Breach Policy
In the event of a data breach, we will:

- Notify affected users within **72 hours**.
- Take immediate steps to secure data and prevent further breaches.
- Notify the relevant authorities.

## Updates to This Policy
We may update this policy from time to time. Any changes will be communicated through our support guild or other appropriate channels. Continued use of AgeVerifier after updates constitutes acceptance of the revised policy.
