---
layout: default
title: idcheck
parent: Commands
nav_order: 5
---
		
<h1>idcheck</h1>
<h6>version: 3.2</h6>
<h6>Documentation automatically generated from docstrings.</h6>

Commands for managing manual ID verification requests.
These tools are for server staff to flag users who require a manual ID check and to manage that status.
Access to these commands is restricted.


### `get`

**Usage:** `/idcheck get <user>`

> Retrieves the ID check status for a specific user.
This command will show you if a user is flagged for a manual ID check, the reason for it, and if they have been verified.
The information is sensitive and will be shown to you privately.

**Permissions:**
- You'll need the `Manage Messages` permission to use this command.

---

### `update`

**Usage:** `/idcheck update <idcheck> <user> <reason>`

> Updates a user's ID check status.
You can use this to manually flag a user for an ID check or to clear their flag after they've been verified.
A reason is required to keep a log of why the status was changed.

**Permissions:**
- You'll need the `Administrator` permission to use this command.

---

### `delete`

**Usage:** `/idcheck delete <user>`

> Removes a user's ID check entry from the database.
This effectively clears their ID check flag. This action is logged for security purposes.

**Permissions:**
- You'll need the `Administrator` permission to use this command.

---

### `create`

**Usage:** `/idcheck create <user> <reason>`

> Flags a user and adds them to the manual ID check list.
This is the first step in requiring a user to provide manual identification. You must provide a reason for this action.
If the user is already on the list, you'll be asked if you want to update their entry.

**Permissions:**
- You'll need the `Manage Messages` permission to use this command.

---

### `send`

**Usage:** `/idcheck send <user>`

> Sends a direct message to a user requesting they provide their ID for verification.
This command will first ask you for a reason, which will be included in the message to the user.
This is a premium feature.

**Permissions:**
- You'll need the `Manage Messages` permission.
- This is a Premium-only command.

---

