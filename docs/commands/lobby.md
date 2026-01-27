---
layout: default
title: Lobby
parent: Commands
nav_order: 6
---
		
<h1>Lobby</h1>
<h6>version: 3.2</h6>
<h6>Documentation automatically generated from docstrings.</h6>

Commands for managing the new member lobby and verification process.
This includes tools for manual verification, age checks, and purging inactive users from the lobby.


### `verify_button`

**Usage:** `/lobby verify_button <text>`

> Creates the main verification button in your lobby channel.
When new users click this button, it kicks off the entire age verification process. You can customize the message that appears above the button.

**Permissions:**
- You'll need `Administrator` permission to use this command.

---

### `idverify`

**Usage:** `/lobby idverify <process> <user> <dob>`

> Manually verifies a user with their ID and date of birth.
This is a powerful tool for whitelisted servers to bypass the standard flow for trusted users.
You can choose whether to put them through the full lobby process or just verify them instantly.

**Permissions:**
- You'll need `Administrator` permission.
- Your server must be whitelisted to use this command.

---

### `returnlobby`

**Usage:** `/lobby returnlobby <user>`

> Moves a user who has already been verified back into the lobby.
This command will remove their verified roles and re-assign the unverified roles, effectively resetting their verification status on this server.

**Permissions:**
- You'll need the `Manage Messages` permission to use this command.

---

### `agecheck`

**Usage:** `/lobby agecheck <dob>`

> Quickly calculates the age based on a given date of birth.
This is a simple utility to check how old someone is without going through the full verification process.

**Permissions:**
- You'll need the `Manage Messages` permission to use this command.

---

### `approve`

**Usage:** `/lobby approve <ctx> <user> <age> <dob>`

> Manually approves a user and grants them access to the server.
This is a prefix command used by moderators to approve a user after a manual review. It logs the approval and assigns the correct roles.

**Permissions:**
- You'll need the `Manage Messages` permission to use this command.

---

### `raid_purge`

**Usage:** `/lobby raid_purge <days>`

> Kicks all users who joined during a suspected raid.
This command looks at the join messages in the lobby channel within a specified number of days and kicks all mentioned users.
You will be asked for confirmation before the purge begins.

**Permissions:**
- You'll need `Administrator` permission to use this command.

---

### `lobby_purge`

**Usage:** `/lobby lobby_purge <days>`

> Kicks users who have been waiting in the lobby for too long.
This command checks the age of the welcome messages in the lobby. If a message is older than the specified number of days, the mentioned user will be kicked.
This helps keep your lobby clean and removes inactive accounts.

**Permissions:**
- You'll need `Administrator` permission to use this command.

---

