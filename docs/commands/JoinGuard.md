---
layout: default
title: JoinGuard
parent: Commands
nav_order: 6
---

<h1>JoinGuard</h1>
<h6>version: 3.3: Updated documentation and quality of life fixes.</h6>
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

