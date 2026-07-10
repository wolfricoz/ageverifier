---
layout: default
title: Configuration Guide
nav_order: 5
---

<!--suppress HtmlDeprecatedAttribute -->
<h1 align="center">Configuration Guide</h1>

This guide explains every setting you can configure for AgeVerifier in plain language. It covers what each option does,
its default value, whether it's a free or premium feature, and anything to watch out for. You don't need any technical
knowledge to follow along — each setting is changed through the bot's slash commands (like `/config`).

> **Tip:** You can see all of your current settings at any time by running `/config view`. Most settings require the *
*Manage Server** permission.

## Free vs. Premium at a glance

Most of AgeVerifier is **free**. The following features require **premium**:

- **Join Requirements** (all the gatekeeping checks, the failure action, and minimum account age)
- **Advanced verification modes** — ID Verification, Basic + ID, and Website verification. (Basic date-of-birth
  verification is free.)
- **The Verification Page** — your customizable web verification page.
- **Automated lobby cleanup & kicking** — the *Clean Lobby Days* and *Kick on Cleanup* settings.
- **Reverification** — including the reverification roles and the reverify log channel.
- **Leave Message** — the notification posted when a member leaves.
- **Leave Survey** — the feedback survey sent to members who leave.

Everything else described in this guide is available on the free plan. Premium items are marked with **💎 Premium**
below.

---

## Welcome & System Messages

These are the messages the bot posts automatically at different points. You write the text yourself, and the bot fills
in details like the user's name and your server name. You can write any of them for free; note that the leave message is
only *sent* when the premium **Send Leave Message** feature is enabled.

| Setting                            | What it does                                                                                                                                                                                         | Default | Plan       |
|------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------|------------|
| **Verification Completed Message** | The welcome message posted in your verification-completed channel once a user finishes verifying. It automatically begins with `Welcome to {server name} {user}!` and then your custom text follows. | Not set | Free       |
| **Server Join Message**            | The very first message a new user sees when they join, posted in your lobby channel. It automatically begins with `Welcome {user}!` followed by your custom text.                                    | Not set | Free       |
| **Server Leave Message**           | The message sent when a user leaves your server. Requires the premium *Send Leave Message* feature to actually be delivered.                                                                         | Not set | 💎 Premium |

---

## Channels

Channels tell the bot *where* to post things. You point each of these at a channel in your server. None of them are set
until you choose one. All are **free** except the **Reverify Age Log**, which is part of the premium reverification
feature.

| Setting                            | What it does                                                                                                                                                                                  | Plan       |
|------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------|
| **Invite Log**                     | Where the bot records invite information (who invited whom).                                                                                                                                  | Free       |
| **Verification Completed Channel** | The channel where the "verification completed" welcome message is posted after a user is verified.                                                                                            | Free       |
| **Server Join Channel (Lobby)**    | Your lobby — the first place new members land. This is where the welcome message appears and where the verification process begins, so it's where new users interact with the bot.            | Free       |
| **Age Log**                        | Where lobby activity is logged. ⚠️ **This channel must be hidden from regular users. If it is visible to them, the bot will leave your server.**                                              | Free       |
| **Approval Channel**               | Where your staff approve verifications. This channel should be hidden from regular users.                                                                                                     | Free       |
| **Verification Failure Log**       | Where failed verification attempts are recorded. Should be hidden from regular users.                                                                                                         | Free       |
| **Reverify Age Log**               | Where re-verification activity is logged. If left unset, it falls back to your regular **Age Log**. ⚠️ **This channel must be hidden from regular users, or the bot will leave your server.** | 💎 Premium |
| **Leave Log**                      | Where member departures are recorded.                                                                                                                                                         | Free       |

> **Important:** The **Age Log** and **Reverify Age Log** channels contain sensitive information. If either one is
> visible to normal members, the bot will automatically leave your server to protect that data. Always double-check
> their
> permissions.

---

## Roles

Roles control what access members get. These settings tell the bot which roles to add or remove at different stages.
None of them are set until you configure them. All are **free** except the **Reverification Role**, which is part of the
premium reverification feature.

| Setting                        | What it does                                                                                                                                                                                              | Plan       |
|--------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------|
| **Verification Add Role**      | Roles given to a user once they successfully verify. These can also be **age roles** with their own age ranges — see the section below.                                                                   | Free       |
| **Verification Remove Role**   | Roles taken away from a user once they successfully verify (often used to remove a "lobby" or "unverified" role).                                                                                         | Free       |
| **Return Remove Role**         | Roles removed when a user runs the `/lobby return` command.                                                                                                                                               | Free       |
| **Server Join Role**           | Roles added the moment a user joins, and automatically removed once they verify their age. Useful for a temporary "newcomer" role.                                                                        | Free       |
| **Auto Update Excluded Roles** | Roles that the automatic age-update system should leave alone. Use this to stop the bot from adding or changing roles you'd rather manage yourself.                                                       | Free       |
| **Reverification Role**        | Roles added to a user when they re-verify their age (e.g. a "Reverified" role). Great for NSFW age gates or servers that added age verification after already having members.                             | 💎 Premium |
| **Approval Ping Role**         | The role that gets pinged when a user submits a verification and is waiting for staff approval. ⚠️ **This does not work with Automatic Verification mode** (there's no manual approval step to ping for). | Free       |

### Age Roles (assigning roles by age)

The **Verification Add Role** setting can do more than hand out a single "verified" role — it can assign different roles
based on how old a member is. When you add a role, you set a **minimum age** and a **maximum age**, and the bot gives
that role only to members whose age falls inside that range.

For example, you could set up:

- an **18–20** role (minimum 18, maximum 20),
- a **21+** role (minimum 21, maximum 200), and
- a general **Verified** role (minimum 18, maximum 200) that everyone who verifies receives.

A member is automatically given every role whose range includes their age. When you add an age role, the defaults are a
**minimum age of 18** and a **maximum age of 200** (effectively "no upper limit") unless you specify otherwise.

If a member's age is **below the minimum of every age role** you've set up, they don't receive any of them — instead the
bot treats them as too young for the server and handles them accordingly (for example, kicking them if *Autokick
Underaged Users* is on). Make sure your lowest age role covers the youngest age you actually allow.

If you also turn on **Auto Update Age Roles** (see *General Toggles*), the bot keeps these roles accurate over time —
for instance moving someone from the 18–20 role into the 21+ role once they get older. Any roles listed under **Auto
Update Excluded Roles** are left untouched by this process.

---

## Verification Modes

You can choose *how* users prove their age. There are two separate settings: one for first-time **Verification** and one
for **Reverification** (when an existing user is asked to verify again).

For each, you can pick one of these methods:

| Method              | What it means                                                                           | Plan       |
|---------------------|-----------------------------------------------------------------------------------------|------------|
| **Basic**           | The user provides their date of birth and age. This is the simplest option.             | Free       |
| **ID Verification** | The user verifies using a photo ID (following safe ID-handling procedures).             | 💎 Premium |
| **All**             | Offers both — the user can verify by date of birth **or** ID, whichever they prefer.    | 💎 Premium |
| **Website**         | Verification is handled through the online dashboard/website instead of inside Discord. | 💎 Premium |

> **Default:** New servers start on **Basic**. Changing the verification mode is a 💎 **premium** feature, so free
> servers stay on Basic date-of-birth verification (which works great on its own).

---

## Join Requirements (Gatekeeping) &nbsp;💎 Premium

These are optional checks the bot runs on **new members as they join**. Each one can be turned on or off individually.
If a member fails an enabled check, the bot takes the action you've chosen (see *Failure Action* below). This whole
section is a **premium** feature, and every check is **off by default**.

| Requirement                  | What it checks                                                                                                                                                                                                   | Plan       |
|------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------|
| **Account Age**              | Whether the account is old enough. You set the minimum in days (see *Minimum Account Age*). Very new accounts are a common sign of spam or ban-evasion.                                                          | 💎 Premium |
| **Has Avatar**               | Whether the account has a profile picture. Accounts with no avatar are flagged. *(If a user recently added an avatar, Discord can take up to ~30 minutes to update, so they may need to wait before rejoining.)* | 💎 Premium |
| **Mutual Guilds**            | Whether the account shares at least one other server in common with the bot. Brand-new throwaway accounts usually share none.                                                                                    | 💎 Premium |
| **Is Bot**                   | Whether the joining account is an unapproved bot. Bots added by a non-administrator are flagged; bots added by an admin are allowed.                                                                             | 💎 Premium |
| **Has Bans**                 | Whether the account has ban records on file (via the bot's ban-tracking system).                                                                                                                                 | 💎 Premium |
| **Require Active Presence**  | Whether the account is actually online. Accounts that appear offline or invisible are flagged.                                                                                                                   | 💎 Premium |
| **Filter Web-Only Accounts** | Flags accounts that are only connected through the web browser client (with no desktop or mobile activity), a pattern often seen with throwaway accounts.                                                        | 💎 Premium |

### Failure Action

**Join Fail Action** decides what happens when a member fails one of the checks above:

- **Log Only** — Record the failure quietly but let the member in.
- **Kick Member** — Remove the member from the server.

### Minimum Account Age

**Minimum Account Age** is the number of days an account must exist to pass the *Account Age* check above. **Default: 7
days.**

---

## Lobby Cleanup

These settings control the automatic tidying of your lobby (removing members who join but never verify). Automated lobby
cleanup is a **premium** feature.

| Setting              | What it does                                                                                                                           | Default      | Plan       |
|----------------------|----------------------------------------------------------------------------------------------------------------------------------------|--------------|------------|
| **Clean Lobby Days** | How many days an inactive, unverified member can sit in the lobby before they're removed. Set to **0 to disable**.                     | 0 (disabled) | 💎 Premium |
| **Kick On Clean**    | When cleanup runs, decides whether inactive members are actually kicked from the server (on) or just cleaned up without kicking (off). | On           | 💎 Premium |

---

## Approval Message Options

When a user's verification is waiting for staff approval, the bot shows an approval card. These toggles control what
information appears on that card, so your staff see exactly what they need to make a decision. All of these are **free
**.

| Option                    | What it shows                                                                         | Default | Plan |
|---------------------------|---------------------------------------------------------------------------------------|---------|------|
| **Large Picture**         | Displays a large version of the user's profile picture.                               | Off     | Free |
| **Small Picture**         | Displays a small profile picture instead (this hides the large one).                  | On      | Free |
| **Bans**                  | Shows the user's ban records before you approve.                                      | On      | Free |
| **Joined At**             | Shows when the user joined *your* server.                                             | On      | Free |
| **Created At**            | Shows when the user's Discord account was created.                                    | On      | Free |
| **User ID**               | Shows the user's account ID number.                                                   | On      | Free |
| **Show Previous Servers** | Shows other servers the user has been in.                                             | Off     | Free |
| **Legacy Message**        | Uses the older style of approval message.                                             | Off     | Free |
| **Debug**                 | Shows a technical debug version of the approval message (mainly for troubleshooting). | Off     | Free |

---

## General Toggles

These are simple on/off switches for major features.

| Toggle                                  | What it does                                                                                                                                                                | Default | Plan       |
|-----------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------|------------|
| **Send Join Message**                   | Turns the lobby welcome message on or off for new members.                                                                                                                  | On      | Free       |
| **Send Verification Completed Message** | Turns the "you're verified" welcome message on or off.                                                                                                                      | On      | Free       |
| **Automatic Verification**              | Lets the bot approve verifications automatically instead of requiring a staff member to approve each one. *(Note: the Approval Ping Role does not apply while this is on.)* | Off     | Free       |
| **Autokick Underaged Users**            | Automatically removes users who don't meet your server's age requirement.                                                                                                   | Off     | Free       |
| **Autokick On Discrepancy**             | Automatically removes a user when the **age** they entered doesn't match the **date of birth** they provided during verification. They're kicked with a message explaining the mismatch and inviting them to appeal to staff. | Off     | Free       |
| **Auto Update Age Roles**               | Automatically keeps members' age-based roles up to date over time. (Respects the *Auto Update Excluded Roles* setting.)                                                     | Off     | Free       |
| **Ping Owner On Failure**               | Notifies the server owner when a verification fails.                                                                                                                        | On      | Free       |
| **Survey**                              | Sends a short survey to members when they leave the server.                                                                                                                 | Off     | 💎 Premium |
| **Log Config Changes**                  | Records whenever a setting is changed, so you have a history of who changed what.                                                                                           | On      | Free       |
| **Cleanup Messages**                    | Automatically tidies up the bot's own messages to keep channels clean.                                                                                                      | On      | Free       |
| **Send Leave Message**                  | Posts a notification to your leave channel whenever a member leaves the server.                                                                                             | Off     | 💎 Premium |
| **Kick On Clean**                       | During automated lobby cleanup, kicks inactive members from the server rather than just clearing them.                                                                      | On      | 💎 Premium |

### Other defaults worth knowing

- **Verification Cooldown** — how long a user must wait between verification attempts (set with `/config cooldown`). *
  *Default: 5 minutes.** Set it to `0` to disable the wait entirely.

---

## Need a hand?

Run `/config view` to see your current settings, and remember that most changes require the **Manage Server**
permission. Anything marked **💎 Premium** is part of AgeVerifier's premium features — everything else works on the free
plan. When in doubt, start with the defaults — they're designed to be safe for most servers.
