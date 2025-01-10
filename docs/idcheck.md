---
layout: default
title: Id Check Management
nav_order: 6
---

<h1>Id Check Management</h1>
When a user fills in the wrong dob, or makes a mistake they are added to the ID list, of course you can do the same manually; when they are added to this list they will be stopped to verify if they try to input their date of birth in any server they join until they have been verified.


## Commands

### `/get`

**Description:** Get the ID check status of the specified user.

**Permissions:** `manage_messages`

**Usage:** /get user:<user or user id>

### `/update`

**Description:** Update the ID check status and reason of the specified user.

**Permissions:** `administrator`

**Usage:**/update user:<user or user id> idcheck:<bool> reason:<reason>

### `/delete`

**Description:** Delete the ID check entry of a specified user.

**Permissions:** `administrator`

**Usage:** /delete user:<user or user id>

### `/create`

**Description:** Adds specified user to the ID list.

**Permissions:** `manage_messages`

**Usage:** /create user:<user or user id> reason:<reason>

## Notes

- The data retrieved or modified by these commands is only allowed to be shared with relevant parties.