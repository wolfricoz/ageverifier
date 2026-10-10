---
layout: default
title: JoinGuard
parent: Commands
nav_order: 6
---

<h1>JoinGuard</h1>
<h6>version: 3.4: Cleaned up and ready to go!</h6>
<h6>Documentation automatically generated from docstrings.</h6>

Commands for configuring security parameters for new users joining the server.
Requires 'Manage Server' permissions.


### `requirements`

**Usage:** `/joinguard requirements <requirement> <status>`

> Toggle individual join requirements like account age, avatar presence, or bot status.

**Permissions:**
- Requires `Manage Server` permission.

---

### `action`

**Usage:** `/joinguard action <penalty>`

> Define what the bot does when an incoming user flags one of your enabled requirements.
Quarantine Role gives them the role set with `/joinguard quarantine` for a set time instead of kicking them.

**Permissions:**
- Requires `Manage Server` permission.

---

### `quarantine`

**Usage:** `/joinguard quarantine <role> <hours>`

> Set the role members get when they fail a join requirement and the action is Quarantine Role, and how many
hours after joining it is taken off again (default 24, up to 720). Use a role only for this: anyone holding it
longer than the duration since they joined has it removed.

**Permissions:**
- Requires `Manage Server` permission.

---

### `minimum_age`

**Usage:** `/joinguard minimum_age <days>`

> Set the minimum age threshold (in days) an account must have to clear the ACCOUNT_AGE check.
Default: 7
**Permissions:**
- Requires `Manage Server` permission.

---

