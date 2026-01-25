
---
layout: default
title: Whitelisting
nav_order: 8
---		
		
<h1>Database</h1>
<h6>version: 3.2</h6>
<h6>Documentation automatically generated from docstrings.</h6>

Commands for interacting with the user database.
Most of these commands are restricted to whitelisted servers and require elevated permissions.


### `stats`

**Usage:** `/database stats`

> Displays various statistics from the bot's database.
This provides a general overview of things like the number of user records, verifications, and active servers.
This information is maintained for administrative purposes and transparency.

**Permissions:**
- You'll need the `Manage Messages` permission to use this command.

---

### `get`

**Usage:** `/database get <user>`

> Looks up and displays the database entry for a specific user.
This includes their stored date of birth and verification status. This command is restricted to whitelisted servers for privacy and security reasons.
The information provided is sensitive and should be handled with care - Do not share it with non-whitelisted parties; they should use the verification system instead or contact support.

**Permissions:**
- You'll need the `Manage Messages` permission.
- Your server must be whitelisted to use this feature.

---

### `create`

**Usage:** `/database create <user> <dob>`

> Manually creates a new database entry for a user with their date of birth.
This is useful for adding users who may have had issues with the automated system. The date of birth should be in `mm/dd/yyyy` format.
This command is restricted to whitelisted servers.

Non-whitelisted servers can use the buttons in the verification system to achieve the same result.

**Permissions:**
- You'll need the `Manage Messages` permission.
- Your server must be whitelisted to use this feature.

---

### `update`

**Usage:** `/database update <user> <dob>`

> Updates the date of birth for a user who is already in the database.
Use this to correct any errors in a user's stored information. The date of birth should be in `mm/dd/yyyy` format.
This command is restricted to whitelisted servers.

Non-whitelisted servers can open a ticket in the support server to have a developer update the user's information.


**Permissions:**
- You'll need the `Manage Messages` permission.
- Your server must be whitelisted to use this feature.

---

### `delete`

**Usage:** `/database delete <user> <reason>`

> Deletes a user's entry from the database.
This should only be used to correct significant mistakes or for privacy requests. A reason for the deletion is required for logging purposes.
This command is restricted to whitelisted servers.

Non-whitelisted servers can open a ticket in the support server to have a developer delete the user's information.

**Permissions:**
- You'll need the `Administrator` permission.
- Your server must be whitelisted to use this feature.

---

