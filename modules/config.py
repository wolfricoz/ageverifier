"""Config options for the bot."""
import os

import discord
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands

from classes import permissions
from classes.databaseController import ConfigTransactions, ConfigData
from views.modals.configinput import ConfigInputUnique
from views.select.configselectroles import *

class config(commands.GroupCog, name="config"):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    messagechoices = ['welcomemessage', "lobbywelcome"]
    channelchoices = ['helpchannel', 'inviteinfo', 'general', "lobby", "lobbylog", "lobbymod",
                      "idlog"]
    rolechoices = {"moderator role": "mod", "administrator role": "admin", 'add to user': 'add', 'remove from user': "rem", "remove on return": "return"}
    available_toggles = ["Welcome", "Automatic"]


    @app_commands.command(name='setup')
    @app_commands.checks.has_permissions(manage_guild=True)
    async def configsetup(self, interaction: discord.Interaction):
        """Sets up the config for the bot."""
        await interaction.response.defer(ephemeral=True)
        for item in self.channelchoices:
            view = ConfigSelectChannels()
            msg = await interaction.channel.send(f"Choose a channel for key: {item}", view=view)
            await view.wait()
            await msg.delete()
            if view.value is None:
                await interaction.followup.send("Setup cancelled")
                return
            ConfigTransactions.config_unique_add(interaction.guild.id, item, int(view.value[0]), overwrite=True)
        for expl,role in self.rolechoices.items():
            view = ConfigSelectRoles()
            msg = await interaction.channel.send(f"{expl}: {role}\nWill add role to the config, if you wish for the old role to be deleted please use the /config role command.", view=view)
            await view.wait()
            await msg.delete()
            if view.value is None:
                await interaction.followup.send("Setup cancelled")
                return
            ConfigTransactions.config_key_add(interaction.guild.id, role, int(view.value[0]), overwrite=True)
        await interaction.followup.send("Config has been set up, please setup the messages with /config messages", ephemeral=True)

    @app_commands.command()
    @app_commands.choices(key=[Choice(name=x, value=x) for x in messagechoices])
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
        await interaction.response.send_message(f"Welcome has been set to {action.value}", ephemeral=True)

    @app_commands.command()
    @app_commands.choices(key=[Choice(name=x, value=x) for x in channelchoices])
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
    @app_commands.choices(key=[Choice(name=ke, value=val) for ke, val in rolechoices.items()])
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

        roles:list = [x for x in self.rolechoices.values()]
        other = ["FORUM", "SEARCH"]
        optionsall = self.messagechoices + self.channelchoices + list(self.available_toggles) + roles
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
