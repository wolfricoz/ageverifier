---
layout: default
title: Database Management
nav_order: 5
---

<h1>Database Management</h1>
To access the database command, your server must be whitelisted; otherwise you can open a ticket on the support server to have a dob changed or looked up

# Database Module

This module handles the lobby-related commands for the bot.

## Commands

### `/get`

**Description:** Gets the date of birth of the specified user.

**Permissions:** `manage_messages`

**Usage:** /get user:<user or user id>

### `/create`

**Description:** Adds the date of birth of the specified user to the database.

**Permissions:** `manage_messages`

**Usage:** /create user:<user or user id> dob:<date_of_birth><

### `/update`

**Description:** Updates the date of birth of a specified user.

**Permissions:** `manage_messages`

**Usage:** /update user:<user or user id> dob:<date_of_birth>

### `/delete`

**Description:** Deletes the date of birth of a specified user. Only use this to correct mistakes.

**Permissions:** `administrator`

**Usage:** /delete user:<user or userid>

## Notes

- The commands are limited to whitelisted servers. If your server is not whitelisted, please join the support server and open a ticket.
- The data retrieved or modified by these commands is only allowed to be shared with relevant parties.
- All changes are logged and may be reviewed in cases of abuse.