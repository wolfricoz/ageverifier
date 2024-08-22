"""Config options for the bot."""
import logging
import os

import discord
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands

from classes import permissions
from classes.databaseController import ConfigTransactions, ConfigData
from views.modals.configinput import ConfigInputUnique
from views.select.configselectroles import *
import classes.whitelist as wl

class whitelist(commands.GroupCog, name="whitelist"):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="add", description="[dev]Adds a guild to the whitelist")
    async def add(self, interaction: discord.Interaction, guild_id: str):
        """Adds a guild to the whitelist"""
        if interaction.user.id != 188647277181665280:
            await interaction.response.send_message("You are not the developer", ephemeral=True)
            return
        wl.add_to_whitelist(guild_id)
        await interaction.response.send_message(f"{guild_id} has been added to the whitelist")

    @app_commands.command(name="remove", description="[dev]Removes a guild from the whitelist")
    async def remove(self, interaction: discord.Interaction, guild_id: str):
        """Removes a guild from the whitelist"""
        if interaction.user.id != 188647277181665280:
            await interaction.response.send_message("You are not the developer", ephemeral=True)
            return
        wl.remove_from_whitelist(guild_id)
        await interaction.response.send_message(f"{guild_id} has been removed from the whitelist")

async def setup(bot: commands.Bot):
    """Adds the cog to the bot"""
    await bot.add_cog(whitelist(bot))
