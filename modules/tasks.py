"""This cogs handles all the tasks."""
import logging
import os
from datetime import datetime, timedelta

import discord
from discord import app_commands
from discord.ext import commands, tasks

from classes import permissions
from classes.databaseController import ConfigData, UserTransactions

OLDLOBBY = int(os.getenv("OLDLOBBY"))


class Tasks(commands.GroupCog):
    def __init__(self, bot):
        """loads tasks"""
        self.bot = bot
        self.index = 0
        self.config_reload.start()
        self.check_users_expiration.start()

    def cog_unload(self):
        """unloads tasks"""
        self.config_reload.cancel()
        self.check_users_expiration.cancel()

    @tasks.loop(hours=1)
    async def config_reload(self):
        """Reloads the config for the latest data."""
        for guild in self.bot.guilds:
            ConfigData().load_guild(guild.id)
        print("config reload")
        ConfigData().output_to_json()

    @tasks.loop(hours=24)
    async def check_users_expiration(self):
        """updates entry time, if entry is expired this also removes it."""
        print("checking user entries")
        userdata = UserTransactions.get_all_users()
        userids = [x.uid for x in userdata]
        removaldate = datetime.now() - timedelta(days=730)
        for guild in self.bot.guilds:
            for member in guild.members:
                if member.id not in userids:
                    UserTransactions.add_user_empty(member.id)
                    continue
                UserTransactions.update_entry_date(member.id)

        for entry in userdata:
            if entry.entry < removaldate:
                UserTransactions.user_delete(entry.uid)
                logging.debug(f"Database record: {entry.uid} expired")

    @app_commands.command(name="expirecheck")
    @permissions.check_app_roles_admin()
    async def expirecheck(self, interaction: discord.Interaction):
        """forces the automatic search ban check to start; normally runs every 30 minutes"""
        await interaction.response.send_message("[Debug]Checking all entries.")
        self.check_users_expiration.restart()
        await interaction.followup.send("check-up finished.")

    @check_users_expiration.before_loop
    async def before_expire(self):
        """stops event from starting before the bot has fully loaded"""
        await self.bot.wait_until_ready()

    @config_reload.before_loop  # it's called before the actual task runs
    async def before_checkactiv(self):
        """stops event from starting before the bot has fully loaded"""
        await self.bot.wait_until_ready()


async def setup(bot):
    """Adds the cog to the bot."""
    await bot.add_cog(Tasks(bot))
