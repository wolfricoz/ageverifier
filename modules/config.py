"""Config options for the bot."""
import logging
import os

from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands

from classes.configsetup import configSetup
from classes.databaseController import ConfigTransactions, ConfigData
from views.modals.configinput import ConfigInputUnique
from views.select.configselectroles import *


class config(commands.GroupCog, name="config"):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    messagechoices = {
        'welcomemessage': 'This is the welcome message that will be posted in the general channel This starts with: `Welcome to {server name} {user}! This is where the message goes`',
        "lobbywelcome"  : 'This is the welcome message that will be posted in the lobby channel, and be the first message new users see. This starts with: `Welcome {user}! This is where the message goes`',
    }
    channelchoices = {
        'inviteinfo': 'This channel will be used to log invite information',
        'general'   : 'This is your general channel, where the welcome message will be posted',
        "lobby"     : 'This is your lobby channel, where the lobby welcome message will be posted. This is also where the verification process will start; this is where new users should interact with the bot.',
        "lobbylog"  : 'This is the channel where the lobby logs will be posted, this channel has to be hidden from the users; failure to do so will result in the bot leaving.',
        "lobbymod"  : 'This is where the verification approval happens, this channel should be hidden from the users.',
        "idlog"     : 'This is where failed verification logs will be posted, this channel should be hidden from the users.'
    }
    rolechoices = {
        "mod"   : "This is the moderator role, these users will be able to approve users",
        "admin" : "Admin role, these users will be able to approve users and change the config, update date of births and id verifications",
        'add'   : 'These roles will be added to the user after a successful verification',
        "rem"   : 'These roles will be removed from the user after a successful verification',
        "return": "These roles will be removed from the user when running the /lobby return command.",
    }
    available_toggles = ["Welcome", "Automatic"]

    @app_commands.command(name='setup')
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.choices(setup_type=[Choice(name=x, value=x) for x in ['manual', 'auto']])
    async def configsetup(self, interaction: discord.Interaction, setup_type: Choice[str]):
        """Sets up the config for the bot."""

        match setup_type.value:
            case 'manual':
                await configSetup().manual(self.bot, interaction, self.channelchoices, self.rolechoices, self.messagechoices)
            case 'auto':
                await configSetup().auto(interaction, self.channelchoices, self.rolechoices, self.messagechoices)

        await interaction.followup.send("The config has been successfully setup, if you wish to check our toggles you please do /config toggles. Permission checking will commence shortly.", ephemeral=True)
        await self.check_channel_permissions(interaction)

    @app_commands.command()
    @app_commands.checks.has_permissions(manage_guild=True)
    async def permissioncheck(self, interaction: discord.Interaction):
        """Checks the permissions of the bot."""
        await interaction.response.send_message(f"Starting to check permissions for all the channels!", ephemeral=True)
        await self.check_channel_permissions(interaction)

    async def check_channel_permissions(self, interaction: discord.Interaction):
        fails = []
        for key in self.channelchoices:
            channel = ConfigData().get_key_or_none(interaction.guild.id, key)
            if channel is None:
                await interaction.channel.send(f"{key} is not set, please set it with /config channels")
                fails.append(key)
                continue
            channel = interaction.guild.get_channel(int(channel))
            if channel is None:
                await interaction.channel.send(f"{key} is not a valid channel, please set it with /config channels")
                fails.append(key)
                continue
            try:
                msg = await channel.send("Checking permissions, if you see this I can post here!")
                await msg.delete()
            except discord.Forbidden:
                await interaction.channel.send(f"I do not have permissions to post in {channel.name}")
                fails.append(key)
                continue
            await interaction.channel.send(f"I have permissions to post in {channel.name}!")
        if len(fails) > 0:
            await interaction.followup.send(f"Failed to check permissions for: {', '.join(fails)}")
            return
        await interaction.followup.send("All permissions are set correctly!")

    @app_commands.command()
    @app_commands.choices(key=[Choice(name=x, value=x) for x, _ in messagechoices.items()])
    @app_commands.choices(action=[Choice(name=x, value=x) for x in ['set', 'Remove']])
    @app_commands.checks.has_permissions(manage_guild=True)
    async def messages(self, interaction: discord.Interaction, key: Choice[str], action: Choice[str]):
        """Sets the messages such as welcome, lobby welcome and reminder messages."""
        match action.value.lower():
            case 'set':
                await interaction.response.send_modal(ConfigInputUnique(key=key.value))
            case 'remove':
                await interaction.response.defer(ephemeral=True)
                result = ConfigTransactions.config_unique_remove(guildid=interaction.guild.id, key=key.value)
                if result is False:
                    await interaction.followup.send(f"{key.value} was not in database")
                    return
                await interaction.followup.send(f"{key.value} has been removed from the database")
            case _:
                raise NotImplementedError

    @app_commands.command()
    @app_commands.choices(action=[Choice(name=x, value=x) for x in ["enabled", "disabled"]], key=[Choice(name=x, value=x) for x in available_toggles])
    @app_commands.checks.has_permissions(manage_guild=True)
    async def toggles(self, interaction: discord.Interaction, key: Choice[str], action: Choice[str]):
        """Enables/Disables the welcome message for the general channel."""
        match action.value.upper():
            case "ENABLED":
                ConfigTransactions.toggle_welcome(interaction.guild.id, key.value, action.value.upper())
            case "DISABLED":
                ConfigTransactions.toggle_welcome(interaction.guild.id, key.value, action.value.upper())
        await interaction.response.send_message(f"{key.value} has been set to {action.value}", ephemeral=True)

    @app_commands.command()
    @app_commands.choices(key=[Choice(name=f"{x} channel", value=x) for x, _ in channelchoices.items()])
    @app_commands.choices(action=[Choice(name=x, value=x) for x in ["set", "remove"]])
    @app_commands.checks.has_permissions(manage_guild=True)
    async def channels(self, interaction: discord.Interaction, key: Choice[str], action: Choice[str],
                       value: discord.TextChannel = None):
        """adds the channels to the config, you can only add 1 value per option."""
        await interaction.response.defer(ephemeral=True)
        if value is not None:
            value = value.id
        match action.value.lower():
            case 'set':
                ConfigTransactions.config_unique_add(guildid=interaction.guild.id, key=key.value, value=value,
                                                     overwrite=True)
                await interaction.followup.send(f"{key.value} has been added to the database with value:\n{value}")
            case 'remove':
                result = ConfigTransactions.config_unique_remove(guildid=interaction.guild.id, key=key.value)
                if result is False:
                    await interaction.followup.send(f"{key.value} was not in database")
                    return
                await interaction.followup.send(f"{key.value} has been removed from the database")
            case _:
                raise NotImplementedError

    @app_commands.command()
    @app_commands.choices(key=[Choice(name=f"{ke} role", value=ke) for ke, val in rolechoices.items()])
    @app_commands.choices(action=[Choice(name=x, value=x) for x in ['add', 'Remove']])
    @app_commands.checks.has_permissions(manage_guild=True)
    async def roles(self, interaction: discord.Interaction, key: Choice[str], action: Choice[str], value: discord.Role):
        """Add roles to the database, for the bot to use."""
        await interaction.response.defer(ephemeral=True)
        value = value.id
        match action.value.lower():
            case 'add':
                result = ConfigTransactions.config_key_add(guildid=interaction.guild.id, key=key.value.upper(),
                                                           value=value, overwrite=False)
                if result is False:
                    await interaction.followup.send(f"{key.name}: <@&{value}> already exists")
                    return
                await interaction.followup.send(f"{key.name}: <@&{value}> has been added to the database")
            case 'remove':
                result = ConfigTransactions.config_key_remove(guildid=interaction.guild.id, key=key.value.upper(),
                                                              value=value)
                if result is False:
                    await interaction.followup.send(f"{key.name}: <@&{value}> could not be found in database")
                await interaction.followup.send(f"{key.name}: <@&{value}> has been removed from the database")
            case _:
                raise NotImplementedError

    @app_commands.command()
    @app_commands.checks.has_permissions(manage_guild=True)
    async def view(self, interaction: discord.Interaction):
        """Prints all the config options"""
        # configoptions = ['welcomemessage', "lobbywelcome", "reminder", "dev", 'helpchannel', 'inviteinfo', 'general', "lobby", "lobbylog", "lobbymod",
        #                  "idlog", "advertmod", "advertlog", "removallog", "nsfwlog", "warnlog", "FORUM", "mod", "admin", "add", "rem", "18", "21", "25", "return", "nsfw", "partner", "posttimeout", "SEARCH"]

        roles: list = [x for x in self.rolechoices.values()]
        other = ["FORUM", "SEARCH"]
        optionsall = list(self.messagechoices) + list(self.channelchoices) + list(self.available_toggles) + list(self.rolechoices)
        await interaction.response.defer()
        with open('config.txt', 'w') as file:
            file.write(f"Config for {interaction.guild.name}: \n\n")
            for item in optionsall:
                info = ConfigData().get_key_or_none(interaction.guild.id, item)
                file.write(f"{item}: {info}\n")
        await interaction.followup.send(f"Config for {interaction.guild.name}", file=discord.File(file.name))
        os.remove(file.name)


async def setup(bot: commands.Bot):
    """Adds the cog to the bot"""
    await bot.add_cog(config(bot))
