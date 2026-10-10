---
layout: default
title: Notes
parent: Commands
nav_order: 8
---

<h1>Notes</h1>
<h6>version: 3.4: Cleaned up and ready to go!</h6>
<h6>Documentation automatically generated from docstrings.</h6>

Commands for keeping staff notes on members.
Notes stay with the member in your server, also when they leave and rejoin, so context carries over between moderators.
The newest notes are shown on the member's approval message; turn this off with `/config approval_toggles staff_notes`.
Notes are only visible to your server's staff and are deleted together with the member's record.


### `add`

**Usage:** `/notes add <user> <note>`

> Adds a note to a member that other staff in this server will see on their approval message and with `/notes list`.
Notes are kept when the member leaves and rejoins.

**Permissions:**
- You'll need the `Manage Messages` permission to use this command.

---

### `list`

**Usage:** `/notes list <user>`

> Shows this server's notes on a member, newest first, with who wrote them and when.
Use the note number with `/notes remove` to delete one.

**Permissions:**
- You'll need the `Manage Messages` permission to use this command.

---

### `remove`

**Usage:** `/notes remove <note_id>`

> Removes a note by its number, as shown by `/notes list`. Only notes written in this server can be removed.

**Permissions:**
- You'll need the `Manage Messages` permission to use this command.

---

