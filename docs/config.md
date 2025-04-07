---
layout: default
title: Setup
nav_order: 2
---

<h1>Config and setup</h1>

RMRbot's setup is relatively painless, and has to only be done once when the bot joins. Since the bot is only
designed for two servers: RMR and RMN. A lot of the setup can be done through the setup command.

for all of the commands below, the permissions guild_manage required to run them.

# USE OUR NEW DASHBOARD FOR EASY SETUP: https://bots.roleplaymeets.com/

## Configuration Options

### Message Choices

- **welcomemessage**: This is the welcome message that will be posted in the general channel. This starts with:
  \`Welcome to {server name} {user}! This is where the message goes\`.
- **lobbywelcome**: This is the welcome message that will be posted in the lobby channel, and be the first message new
  users see. This starts with: \`Welcome {user}! This is where the message goes\`.

### Channel Choices

- **inviteinfo**: This channel will be used to log invite information.
- **general**: This is your general channel, where the welcome message will be posted.
- **lobby**: This is your lobby channel, where the lobby welcome message will be posted. This is also where the
  verification process will start; this is where new users should interact with the bot.
- **lobbylog**: This is the channel where the lobby logs will be posted. This channel has to be hidden from the users;
  failure to do so will result in the bot leaving.
- **lobbymod**: This is where the verification approval happens. This channel should be hidden from the users.
- **idlog**: This is where failed verification logs will be posted. This channel should be hidden from the users.

### Role Choices

- **add**: These roles will be added to the user after a successful verification.
- **rem**: These roles will be removed from the user after a successful verification.
- **return**: These roles will be removed from the user when running the `/lobby return` command. (Not required, not in setup)

### Toggle Options (Not in setup)

- **welcome**: This command will enable or disable the welcome message.
- **automatic**: This command will enable or disable the automatic age verification.


## `/config setup`

This command will run you through the setup process of setting up the channels and roles for the bot to function
properly. It will run through all the options above, except for the toggle options and the role choice 'return'.

## `/config messages key:option action:(set/remove) `

after entering the config messages command you will be prompted with a modal to input the message you wish to have
displayed for the option you have chosen. The options are as follows:

* welcomemessage
* lobbymessage
* reminder

## `/config toggle key:option action:(enable/disable)`

Options:

* welcome: This command will enable or disable the welcome message.
* automatic: This command will enable or disable the automatic age verification.

## `/config channels key:option action:(set/remove) value:(channel)`

This command will set the channel for the option you have chosen. the value will display discord.TextChannel objects to
choose from. the channel name is the name of the channel, for
example: `/config channels key:lobby action:set value:lobby`

## `/config role key:option action:(set/remove) value:(role)`

This command will set the role for the option you have chosen. the value will display discord.Role objects to choose
from.

## `/config view`

Allows you to view the current configuration of the server. This command is not required to be run, but is useful to see
what the current configuration is.

## `/config cooldown cooldown:(number)`

This command allows you to set or remove the cooldown period for specific actions within the server. The cooldown period is specified in minutes. If the cooldown is set to 0, it is disabled.

