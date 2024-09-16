"""Config options for the bot."""
import asyncio
import logging
import os

import discord
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands

from classes import permissions
from classes.databaseController import ConfigTransactions, ConfigData
from views.modals.configinput import ConfigInputUnique
from views.modals.inputmodal import send_modal
from views.select.configselectroles import *
import classes.whitelist as wl

class dev(commands.GroupCog, name="dev"):

    def __init__(self, bot: commands.Bot):
        self.bot = bot


    async def create_invite(self, guild: discord.Guild):
        print(guild.id)
        try:
            config = ConfigData().get_key_int(guild.id, "lobbymod")
            invite = await guild.get_channel(config).create_invite(max_age=604800)
        except discord.Forbidden:
            invite = 'No permission'
        except Exception as e:
            invite = f'No permission/Error'
            logging.error(f"Error creating invite: {e}")
        return invite

    @app_commands.command(name="announce", description="[DEV] Send an announcement to all guild owners")
    async def announce(self, interaction: discord.Interaction):
        message = await send_modal(interaction, "What is the announcement?", "Announcement", 1700)
        if interaction.user.id != int(os.getenv('DEVELOPER')):
            await interaction.response.send_message("You are not a developer", ephemeral=True)
            return
        bot = self.bot
        supportguild = bot.get_guild(int(os.getenv('SUPPORTGUILD')))
        support_invite = await self.create_invite(supportguild)
        announcement = (f"## AGE VERIFIER ANNOUNCEMENT"
                        f"\n{message}"
                        f"\n-# You can join our support server by [clicking here to join]({support_invite}). If you have any questions, errors or concerns, please open a ticket in the support server.")

        for guild in self.bot.guilds:
            await asyncio.sleep(1)
            try:
                configid = ConfigData().get_key_int(guild.id, "lobbymod")
                channel = self.bot.get_channel(configid)
                await channel.send(announcement)
            except Exception as e:
                try:
                    await guild.owner.send(
                            f"Age Verifier could not send the announcement to your lobbymod in {guild.name}, please check the mod channel settings. You can setup your lobbymod with: ```/config channels key:lobbymod action:set value:```")
                    await guild.owner.send(announcement)
                except Exception as e:
                    await interaction.channel.send(f"Error sending to {guild}({guild.owner}): {e}")

async def setup(bot: commands.Bot):
    """Adds the cog to the bot"""
    await bot.add_cog(dev(bot))
