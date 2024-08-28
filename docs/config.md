---
layout: default
title: Setup
nav_order: 6
---

<h1>Config and setup</h1>

RMRbot's setup is relatively painless, and has to only be done once when the bot joins. Since the bot is only
designed for two servers: RMR and RMN. A lot of the setup can be done through the setup command.

for all of the commands below, the permissions guild_manage required to run them.

## `/config setup`

This command will run you through the setup process of setting up the channels and roles for the bot to function
properly.
To setup setup the welcoming messages, search options and ban options will need to be done through the config command
independently.

Please note that the setup command will not set the welcome message, search commands or ban commands. These will need to
be set independently. You must also ensure that the bot has the correct permissions to send messages in the channels you
have set up.

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



