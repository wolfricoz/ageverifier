---
layout: default
title: Permissions Guide
nav_order: 7
---

<!--suppress HtmlDeprecatedAttribute -->
<h1 align="center">Permissions Guide</h1>

For AgeVerifier to do its job — welcoming new members, assigning roles, cleaning the lobby, and removing users who don't meet your age requirement — it needs the right permissions in your Discord server. This guide explains, in plain language, exactly which permissions the bot needs, *why* it needs each one, and how to grant them.

> **The short version:** the simplest and most reliable setup is to give AgeVerifier a role with **Manage Roles**, **Kick Members**, **Manage Messages**, **View Audit Log**, and the standard messaging permissions (**View Channels**, **Send Messages**, **Embed Links**, **Attach Files**, **Read Message History**), and to place that role **above** the roles it needs to hand out.

---

## How Discord permissions work (a quick primer)

Discord permissions are abilities you grant to **roles**, and roles are attached to members (including bots). When AgeVerifier joins your server, it's given its own role. Whatever that role is allowed to do, the bot can do.

According to [Discord's official permissions documentation](https://discord.com/developers/docs/topics/permissions), there are two layers to keep in mind:

1. **Server-level (base) permissions** — set on a role, these apply everywhere in the server.
2. **Channel-level overwrites** — a specific channel can *allow* or *deny* a permission for a role, overriding the server-level setting for that one channel.

This means a bot can have a permission server-wide but still be blocked in one channel if that channel denies it (and vice-versa). If AgeVerifier works in most places but not one specific channel, a channel overwrite is almost always the cause.

There's also a **role hierarchy**. Discord's docs are explicit about this: *"A bot can only kick, ban, and edit nicknames for users whose highest role is lower than the bot's highest role,"* and a bot *"can grant roles to other users that are of a lower position than its own highest role."* In plain terms: **AgeVerifier's role must sit above any member it needs to manage and above any role it needs to assign.** This is the single most common cause of "the bot isn't working" reports.

---

## Permissions AgeVerifier needs

Below is each permission the bot uses, what it's for, and how important it is. The official name (as it appears in Discord's API) is shown in brackets.

### Essential permissions

These are needed for core verification to work at all.

| Permission | Why AgeVerifier needs it |
|---|---|
| **View Channels** (`VIEW_CHANNEL`) | To see your lobby, log, and approval channels so it can read and post in them. Without it, the bot is effectively blind to a channel. |
| **Send Messages** (`SEND_MESSAGES`) | To post welcome messages, the verification prompt, log entries, and approval cards. |
| **Read Message History** (`READ_MESSAGE_HISTORY`) | To review earlier messages in the lobby — for example, when cleaning up members who joined long ago but never verified. |
| **Embed Links** (`EMBED_LINKS`) | The approval cards and many of the bot's messages are sent as rich embeds; without this permission they won't display. |
| **Attach Files** (`ATTACH_FILES`) | To upload files such as the full configuration export from `/config view`, and images used during ID verification. |
| **Manage Roles** (`MANAGE_ROLES`) | The heart of the bot: adding your "verified" and age-based roles once a member passes, and removing lobby/unverified roles. ⚠️ AgeVerifier can only manage roles **positioned below its own role** — see *Role hierarchy* below. |
| **Kick Members** (`KICK_MEMBERS`) | To remove members who fail verification, who are under your age requirement (when *Autokick* is on), or who sit inactive in the lobby past your cleanup window. |

### Recommended permissions

Needed for specific features. If you don't use the related feature, you can skip these — but the feature won't work without them.

| Permission | Why AgeVerifier needs it |
|---|---|
| **Manage Messages** (`MANAGE_MESSAGES`) | To tidy up the bot's own messages and clean up leftover lobby messages (used by *Cleanup Messages* and the lobby purge tools). |
| **Manage Server** (`MANAGE_GUILD`) | To read your server's invites, which powers the invite-tracking / invite-log feature. If the bot lacks this, it will message the server owner to let them know it's missing. |
| **View Audit Log** (`VIEW_AUDIT_LOG`) | Used by the *Is Bot* join check to see **who added** a bot to your server, so bots added by non-administrators can be flagged. |
| **Ban Members** (`BAN_MEMBERS`) | Only required if you use AgeVerifier's moderation/ban actions. Not needed for standard age verification. |

> **A note on Administrator:** granting **Administrator** would cover every permission above in one click, but Discord and general security best practice recommend **against** it. It's safer to grant only the permissions listed here, so the bot can never do more than it needs to.

---

## Privileged Gateway Intents

Separate from channel/role permissions, Discord has three **privileged intents** — special switches that let a bot receive certain sensitive information. These are toggled in the [Discord Developer Portal](https://discord.com/developers/applications), not in your server. If you're **adding AgeVerifier through its official invite link, these are already handled for you** — this section is mainly for transparency and for anyone self-hosting the bot.

AgeVerifier relies on:

- **Server Members Intent** — so the bot is notified when members join and leave. This drives the entire lobby and verification flow.
- **Message Content Intent** — so the bot can read message content where needed for its commands and lobby processing.
- **Presence Intent** *(optional)* — only needed for the two premium join checks that look at whether an account is online: *Require Active Presence* and *Filter Web-Only Accounts*. If this intent isn't enabled, those two checks are simply skipped and everything else keeps working.

You can read Discord's official explanation of these on the [Gateway Intents documentation](https://discord.com/developers/docs/events/gateway#privileged-intents).

---

## Check everything at once with `/config permissioncheck`

You don't have to verify all of this by hand. AgeVerifier has a built-in command that inspects your setup and reports back exactly what's right and what's missing:

```
/config permissioncheck
```

*(Requires the **Manage Server** permission to run.)*

When you run it, the bot posts two summary cards — usually in your approval/log channel:

- **Permissions Check (channels)** — goes through every channel you've configured (lobby, approval channel, log channels, and so on) and confirms the bot has **View Channel**, **Send Messages**, **Embed Links**, and **Attach Files** in each. Anything missing is listed with a ❌, and channels you haven't set yet are flagged as "not set."
- **Permissions Check (roles)** — confirms the bot has **Manage Roles** overall, then checks each role you've configured (including your age roles) to make sure it sits **below** AgeVerifier's own role so the bot can actually assign it. Roles the bot can't manage are flagged with a ❌.

This is the fastest way to diagnose problems: run it any time the bot isn't behaving as expected, after you set up your channels and roles, or whenever you move roles around. In fact, if verification ever fails because of a permission problem, the bot itself will point you to this command.

> **Tip:** Run `/config permissioncheck` right after your initial setup, then again any time you add a new channel or role — it takes seconds and catches the most common mistakes.

---

## Role hierarchy: the #1 thing to get right

Because of Discord's role-hierarchy rules, **where you place AgeVerifier's role in your role list matters as much as which permissions it has.**

Picture your server's roles as a stacked list in **Server Settings → Roles**. A bot can only:

- assign or remove roles that are **below** its own role, and
- kick members whose **highest** role is **below** its own role.

So if your "Verified" role or "18+" role sits *above* AgeVerifier's role, the bot won't be able to hand it out — even though it has Manage Roles. The fix is to **drag AgeVerifier's role higher up**, above every role it needs to give out and above the members it needs to manage.

> **Rule of thumb:** put AgeVerifier's role near the top of your list — below your admin/owner roles, but above all the verification, age, and member roles it works with.

---

## How to set permissions (step by step)

### Option 1 — When first adding the bot

When you click AgeVerifier's invite link, Discord shows an authorization screen listing the permissions being requested. Review them, make sure the correct server is selected, and approve. Discord will create a role for the bot with those permissions automatically.

### Option 2 — Adjusting permissions on the bot's role

1. Open **Server Settings** (click your server name → *Server Settings*).
2. Go to the **Roles** tab.
3. Find and click **AgeVerifier's role** in the list.
4. Under **Permissions**, toggle on the permissions listed in this guide (or confirm they're already on).
5. **Drag the role upward** so it sits above the roles the bot must assign and the members it must manage.
6. Save your changes.

### Option 3 — Fixing a single channel

If the bot works everywhere except one channel (for example, it can't post in your lobby):

1. Right-click the channel → **Edit Channel** → **Permissions**.
2. Add **AgeVerifier's role** (or the bot itself) to the list.
3. Make sure **View Channel** and **Send Messages** are set to **allow** (green ✓), not deny.
4. Save.

This is because a channel-level **deny** overwrite beats a server-level allow, as described in Discord's permissions documentation.

---

## Quick troubleshooting

Not sure where the problem is? Run **`/config permissioncheck`** first — it will tell you which channel or role is misconfigured. Then use this table to interpret the result:

| Symptom | Most likely cause |
|---|---|
| Bot won't assign the verified/age role | AgeVerifier's role is **below** the role it's trying to give out — move its role higher. |
| Bot can't kick underage or failed members | Same hierarchy issue, or **Kick Members** is missing. |
| Bot is silent in one specific channel | A **channel overwrite** is denying View Channel or Send Messages there. |
| Approval cards show as blank/plain text | **Embed Links** is missing. |
| `/config view` or ID images won't upload | **Attach Files** is missing. |
| Invite logging isn't working | **Manage Server** is missing (the bot will DM the owner about this). |
| The *Is Bot* join check never flags anything | **View Audit Log** is missing. |
| Online/web-only join checks do nothing | The **Presence Intent** isn't enabled (premium checks only). |

---

## Sources

- [Discord Developer Documentation — Permissions](https://discord.com/developers/docs/topics/permissions)
- [Discord Developer Documentation — Gateway (Privileged Intents)](https://discord.com/developers/docs/events/gateway#privileged-intents)
