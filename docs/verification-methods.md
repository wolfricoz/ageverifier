---
layout: default
title: Verification Methods
nav_order: 6
---

<!--suppress HtmlDeprecatedAttribute -->
<h1 align="center">Verification Methods</h1>

AgeVerifier can confirm a member's age in a few different ways. This page explains each method, what it means for your
members, and when to choose it. You set the method with `/config verification_mode`.

> You can set the method separately for first-time **Verification** and for **Reverification** (asking existing members
> to verify again). Changing the method is a **premium** feature; **Basic** is the free default and is all many servers
> ever need.

---

## Basic &nbsp;·&nbsp; Free

The member enters their **date of birth** and **Age** in a private pop-up, and the bot calculates their age. When a user
gives
their age, the bot checks if they previously have submitted their date of birth and if that matches as well as a few
additional
checks to ensure they provided their actual date of birth.

**This is the default for every new server.**

**Choose this when:** you want a simple, low-friction check that keeps most people moving through quickly. It's the
right starting point for the vast majority of communities.

## ID Verification &nbsp;·&nbsp; 💎 Premium

The member confirms their age using a **photo ID**, following safe ID-handling practices (blacking out everything except
the date of birth, and removing the image afterward). AgeVerifier never stores the ID itself — only the date of birth.

**Choose this when:** you need a higher level of assurance than a self-entered date, for example in servers with
stricter access requirements. Make sure your staff understand safe ID handling before enabling it — see
the [Whitelisting](whitelisting.html) page for the etiquette and legal considerations.

## All (Basic + ID) &nbsp;·&nbsp; 💎 Premium

Combines both: the member provides a **date of birth *or*** verifies with ID. This option gives your members the most
options!

**Choose this when:** Choose this if you want to give your members all the possible options.

## Website Verification &nbsp;·&nbsp; 💎 Premium

Verification happens through the **web dashboard** instead of inside Discord. The member is directed to the site to
complete the process.

The verification page is a fully customizable page, allowing you to upload your own images, edit colors, add a lovely
intro to your server and display your rules in style!

**Choose this when:** you prefer to handle verification outside of Discord's chat flow, or want the more guided
experience the website provides. See the [Dashboard](dashboard.html) page for more on the web experience.

---

## Quick comparison

| Method              | What the member does          | Plan       | Best for                      |
|---------------------|-------------------------------|------------|-------------------------------|
| **Basic**           | Enters date of birth          | Free       | Most servers; fast and simple |
| **ID Verification** | Provides a photo ID           | 💎 Premium | Higher assurance              |
| **All**             | Date of birth **OR** ID       | 💎 Premium | Maximum thoroughness          |
| **Website**         | Verifies on the web dashboard | 💎 Premium | Guided, out-of-Discord flow   |

---

## A note on Reverification

**Reverification** asks members who are *already* in your server to verify again — commonly used to gate NSFW or
otherwise restricted areas. It uses the same methods above, always runs automatically, and adds a single dedicated role
on success. Reverification is a premium feature; see the [Reverify command reference](commands/Reverify.html) for setup.

---

Related
reading: [Configuration Guide](configuration.html#verification-modes) · [Verifying Your Age (member view)](verifying.html) · [Premium](premium.html)
