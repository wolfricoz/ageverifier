---
layout: default
title: Getting Started
nav_order: 2
---

<!--suppress HtmlDeprecatedAttribute -->
<h1 align="center">Getting Started</h1>

This guide takes you from an empty server to a working age-verification setup, step by step. If you follow it in order, you'll have new members being welcomed, verified, and given the right roles by the end.

> **In a hurry?** The fastest route is the web dashboard: run `/config configsetup` and choose **dashboard**, or head straight to the [dashboard](https://strykerdevelopment.com). It walks you through everything below with a point-and-click interface. This page covers the in-Discord method so you understand what each piece does.

---

## Step 1 — Invite the bot

Add AgeVerifier to your server using its invite link. On the authorization screen, keep the requested permissions enabled — they're what the bot needs to assign roles, welcome members, and keep your lobby tidy. If you're curious about exactly what each permission is for, see the [Permissions Guide](Permissions.html).

## Step 2 — Position the bot's role

This is the single most important step, and the most common thing people miss.

Open **Server Settings → Roles** and drag **AgeVerifier's role near the top of your list** — below your admin/owner roles, but **above every role the bot needs to hand out** (your verified role, age roles, etc.) and above the members it needs to manage. Discord won't let a bot assign a role that sits higher than its own, so if this is wrong, verification will appear to "do nothing." The [Permissions Guide](Permissions.html) explains the hierarchy rule in more detail.

## Step 3 — Run the setup command

In any channel the bot can see, run:

```
/config configsetup
```

You'll be offered three ways to set up:

- **dashboard** — gives you a link to the web dashboard for a graphical setup (recommended).
- **auto** — automatically creates the channels and roles the bot needs, so you can be running in seconds.
- **manual** — walks you through it step by step inside Discord.

If you're not sure, **auto** is the quickest way to a working baseline that you can fine-tune afterward.

## Step 4 — Set your channels

AgeVerifier posts different things in different places. At minimum you'll want a **lobby** (where new members land and verify) and the hidden **log/approval** channels. Set each one with:

```
/config channels
```

⚠️ **Two channels must be hidden from regular members: the Age Log and the Reverify Age Log.** If either is visible to normal users, the bot will leave your server to protect the sensitive information posted there. Double-check their permissions. The full list of channels and what each is for lives in the [Configuration Guide](configuration.html#channels).

## Step 5 — Set your roles (and age roles)

Tell the bot which roles to add and remove when someone verifies:

```
/config roles
```

When you add a **Verification Add Role**, you can also give it a **minimum and maximum age**, which turns it into an *age role* — for example an 18–20 role and a separate 21+ role. Members automatically receive every role whose age range fits them. See [Age Roles](configuration.html#age-roles-assigning-roles-by-age) for how to set these up (and what happens if someone is below your youngest age role).

## Step 6 — Create the verification button

Put the button members will click to start verifying into your lobby channel:

```
/lobby verify_button
```

You can customize the message that appears above the button. This is the entry point to the whole process — from here, members follow the flow described in [Verifying Your Age](verifying.html).

## Step 7 — Choose how members verify (optional)

By default, verification is **Basic** (members enter their date of birth), which is free and works well for most servers. If you have premium and want ID or website-based verification, set it with:

```
/config verification_mode
```

See [Verification Methods](verification-methods.html) for a breakdown of each option.

## Step 8 — Check your permissions

Before you announce anything, let the bot audit your setup:

```
/config permissioncheck
```

It posts two summary cards showing whether it has the right access in each channel and whether it can assign each of your roles. Fix anything marked with a ❌ (usually a role that needs to move higher, or a channel permission). Re-run it any time you add a channel or role.

## Step 9 — Test it

The best test is a real one: join with an alternate account (or ask a trusted member) and go through the flow. You should see the welcome message, be able to click the button, enter a date of birth, and — once approved — receive your verified role. If something doesn't work, the [FAQ & Troubleshooting](faq.html) page covers the usual culprits.

---

## Recommended toggles to review

Once the basics work, skim `/config toggles` and decide which of these you want:

- **Automatic Verification** — approve members automatically instead of having staff approve each one.
- **Autokick Underaged Users** — remove anyone below your age requirement automatically.
- **Auto Update Age Roles** — keep age roles accurate as members get older.
- **Send Join / Verification Completed Messages** — control which welcome messages are posted.
- **Send Leave Message** *(premium)* — post a note when a member leaves.

Every toggle, its default, and whether it's free or premium is documented in the [Configuration Guide](configuration.html#general-toggles).

---

## Where to go next

- [Configuration Guide](configuration.html) — every setting explained.
- [Verification Methods](verification-methods.html) — Basic vs. ID vs. Website.
- [Permissions Guide](Permissions.html) — what the bot needs and how to grant it.
- [FAQ & Troubleshooting](faq.html) — quick fixes for common issues.
- Need a hand? Join the [support server](https://discord.gg/twbegvvarY).
