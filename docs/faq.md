---
layout: default
title: FAQ & Troubleshooting
nav_order: 11
---

<!--suppress HtmlDeprecatedAttribute -->
<h1 align="center">FAQ &amp; Troubleshooting</h1>

Quick answers to the questions that come up most often. If something isn't covered here, the [support server](https://discord.gg/twbegvvarY) is the best place to ask.

> **First stop for any "the bot isn't working" issue:** run `/config permissioncheck`. It audits your channels and roles and tells you exactly what's misconfigured. Most problems are solved right there.

---

## Setup & permissions

**The bot won't give members their role after they verify.**
Almost always a role-position problem. AgeVerifier can only assign roles that sit **below** its own role. Open **Server Settings → Roles** and drag the bot's role above your verified/age roles. See the [Permissions Guide](Permissions.html#role-hierarchy-the-1-thing-to-get-right).

**The bot can't kick members who fail or are underage.**
Same hierarchy rule (the bot can only kick members whose highest role is below its own), or it's missing the **Kick Members** permission.

**The bot is silent in one specific channel.**
That channel has a permission overwrite denying **View Channel** or **Send Messages**. Edit the channel's permissions and allow them for the bot's role.

**Approval cards show up blank or as plain text.**
The bot is missing **Embed Links** in that channel.

**Invite logging isn't working.**
The bot needs the **Manage Server** permission to read your server's invites.

## "The bot left my server!"

This is a safety feature, not a bug. The **Age Log** and **Reverify Age Log** channels contain sensitive information, so they **must be hidden from regular members**. If either becomes visible to everyone, the bot leaves automatically to protect that data. Re-invite the bot, then make sure those channels are staff-only before configuring them. See [Configuration → Channels](configuration.html#channels).

## Verifying members

**A member says the date-of-birth form won't accept their entry.**
The default format is **`MM/DD/YYYY`** but using the buttons they can choose their own format (and the dashboard takes their regional format automatically!). If you do any of the commands using ageverifier you have to submit them in `mm/dd/yyyy`.

**A member got a cooldown message.**
Servers can set a short wait between verification attempts to prevent spam. They just need to wait a few minutes and try again. You can adjust or disable this with `/config cooldown` (set it to `0` to turn it off).

**A join check is flagging a member for having no avatar, but they have one.**
Discord can take up to ~30 minutes to sync a newly changed avatar. Ask them to wait, then rejoin/retry.

**A member is already verified in another server — do they need to redo it?**
The system may recognize them and check that the date of birth they give is consistent with what's on record. They should always provide the same, accurate date. If the user has ID verified in the past then they no longer need to input their details again because ageverifier will do so automatically.

**Online/presence-based join checks (Require Active Presence, Filter Web-Only Accounts) aren't doing anything.**
Those rely on the **Presence Intent**, which is separate from server permissions. If it isn't enabled for the bot, those two checks are skipped while everything else keeps working. Please inform the Devs that you're having issues!

## Roles & ages

**A member's age doesn't match any of my age roles.**
If someone is below the minimum age of *every* age role you've set, they receive none of them and are treated as too young for the server (and kicked if Autokick is on). Make sure your lowest age role covers the youngest age you allow. See [Age Roles](configuration.html#age-roles-assigning-roles-by-age).

**Ages aren't updating as members get older.**
Turn on **Auto Update Age Roles**. Any roles you list under **Auto Update Excluded Roles** are intentionally left untouched.

## Premium & data

**How do I get premium, and what does it include?**
Premium is purchased per-server on the [dashboard](https://strykerdevelopment.com). See the [Premium](premium.html) page for the full feature list.

**How long does it take for premium to sync?**
Premium takes up to one hour to sync to the bots, if it takes longer than one hour please contact `ricostryker` on discord.

**A member wants their data removed.**
They can run `/gdpr removal` themselves (removed after a 30-day grace period), or request a copy with `/gdpr data`. Details are in the [Privacy Policy](privacypolicy.html).

**Can I edit a member's stored date of birth?**
Correcting stored data is available to whitelisted servers via the `/database` commands; other servers can open a ticket in the [support server](https://discord.gg/twbegvvarY). See [Whitelisting](whitelisting.html).

---

## Still stuck?

Run `/config permissioncheck`, skim the [Permissions Guide](Permissions.html), and if you're still blocked, bring the details to the [support server](https://discord.gg/twbegvvarY) — including what you expected to happen and what actually happened.
