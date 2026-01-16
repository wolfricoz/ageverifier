
---
layout: default
title: Whitelisting
nav_order: 8
---		
		
<h1>Config</h1>
<h6>version: 3.2</h6>
<h6>Documentation automatically generated from docstrings.</h6>

Commands for configuring the bot's settings in the server.
This includes setting up channels, roles, custom messages, and feature toggles.
Most commands require 'Manage Server' permissions.


### `configsetup`

**Usage:** `/config configsetup <setup_type>`

> This command helps you get the bot set up on your server. You have a few options to choose from:
'dashboard' will give you a link to our web dashboard for an easy, graphical setup experience.
'manual' will guide you step-by-step through the setup process using Discord commands.
'auto' will automatically create the necessary roles and channels to get the bot running quickly.

**Permissions:**
- You'll need the `Manage Server` permission to use this command.
- The bot needs `Send Messages`, `Embed Links`, and `View Channel` permissions in the channel where you run this command.

---

### `permissioncheck`

**Usage:** `/config permissioncheck`

> This command triggers a check to ensure the bot has all the necessary permissions in the channels you've configured for it.
It's a great way to diagnose problems if the bot isn't behaving as expected. Any issues found will be reported, usually in your log channel.

**Permissions:**
- You'll need the `Manage Server` permission to use this command.

---

### `messages`

**Usage:** `/config messages <key> <action>`

> Lets you customize the various messages the bot sends. You can either set a new custom message or remove an existing one to revert it back to the default.
When you choose to 'set' a message, a pop-up will appear for you to enter your new text.


**Permissions:**
- You'll need the `Manage Server` permission to use this command.

---

### `toggles`

**Usage:** `/config toggles <key> <action>`

> This command allows you to enable or disable various features of the bot.
You can turn things on or off to best suit your server's needs.

**Permissions:**
- You'll need the `Manage Server` permission to use this command.

---

### `approval_toggles`

**Usage:** `/config approval_toggles <key> <action>`

> Use this command to customize the buttons that appear on the verification approval message in your log channel.
This allows you to enable or disable specific actions your moderators can take, like banning or noting a user's ID.

I highly recommend using the website, as it provides a more user-friendly interface for configuring these settings. You can see the changes in real-time and understand the impact of each toggle better.

**Permissions:**
- You'll need the `Manage Server` permission to use this command.

---

### `channels`

**Usage:** `/config channels <key> <action> <value>`

> This command is for assigning specific channels for the bot's functions, like a channel for logging or a lobby for new members.
You can either 'set' a new channel or 'remove' an existing assignment.


**Permissions:**
- You'll need the `Manage Server` permission to use this command.

---

### `roles`

**Usage:** `/config roles <key> <action> <value> <minimum_age> <maximum_age>`

> Use this command to manage which roles the bot interacts with. You can configure roles to be assigned upon verification,
including setting minimum and maximum age requirements for specific roles.


**Permissions:**
- You'll need the `Manage Server` permission to use this command.

---

### `cooldown`

**Usage:** `/config cooldown <cooldown>`

> Set a cooldown period for how often a user can attempt verification in the lobby.
This can help prevent spam. The cooldown is set in minutes. You can set it to 0 to disable the cooldown entirely.

**Permissions:**
- You'll need the `Manage Server` permission to use this command.

---

### `view`

**Usage:** `/config view <guild>`

> This command provides a complete overview of the bot's current configuration for your server.
It's a handy way to see all your settings at a glance. The configuration will be sent as a text file.

**Permissions:**
- You'll need the `Manage Server` permission to use this command.
- Only the bot developer can view the configuration of other guilds.

---

### `cache`

**Usage:** `/config cache <ctx>`

> This is a developer-only command used for internal purposes, specifically for caching message history from a channel.
It is not intended for regular server administrators.

                        -- RMR LEGACY COMMAND, ONE TIME USE --

**Permissions:**
- This command can only be used by the bot's owner.

---

