---
layout: default
title: Reverify
parent: Commands
nav_order: 7
---		
		
<h1>Reverify</h1>
<h6>version: 3.2</h6>
<h6>Documentation automatically generated from docstrings.</h6>

<h3>Premium Feature: Reverify</h3>

Reverification is the process of asking existing members to verify themselves again to gain access to certain channels or roles. This is often used in servers with NSFW content or other restricted areas to ensure that members still meet the requirements for access. By using reverification, server admins can maintain a safe and compliant environment for their members, while also providing an additional layer of security against potential rule violations. This uses the same verification system as the initial verification process, except it only adds one role upon successful verification and is always automatic.

Configurations needed to use reverification:
- reverification_role
- all of the verification configs


### `create`

**Usage:** `/reverify create <channel> <desc_text>`

> Creates the button to start the secondary verification

This command creates a button in the specified channel that users can click to start the secondary verification process, which assigns them the reverification role upon successful verification.

**Permissions:**
- You need to have the `Manage Guild` permission to use this command.
- Premium access is required to use this feature.

---

