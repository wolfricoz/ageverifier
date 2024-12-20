"""This cogs handles all the tasks."""
import asyncio
import logging
import os
from datetime import datetime, timedelta

import discord
from discord import app_commands
from discord.ext import commands, tasks

from classes import permissions
from classes.databaseController import ConfigData, ServerTransactions, UserTransactions

OLDLOBBY = int(os.getenv("OLDLOBBY"))


class Tasks(commands.GroupCog):
    def __init__(self, bot):
        """loads tasks"""
        self.bot = bot
        self.index = 0
        self.config_reload.start()
        self.check_users_expiration.start()
        self.check_active_servers.start()
    def cog_unload(self):
        """unloads tasks"""
        self.config_reload.cancel()
        self.check_users_expiration.cancel()
        self.check_active_servers.cancel()


    @tasks.loop(hours=1)
    async def config_reload(self):
        """Reloads the config for the latest data."""
        for guild in self.bot.guilds:
            ConfigData().load_guild(guild.id)
        print("config reload")
        ConfigData().output_to_json()
        for guild in self.bot.guilds:

            try:
                self.bot.invites[guild.id] = await guild.invites()
            except discord.errors.Forbidden:
                print(f"Unable to get invites for {guild.name}")
                try:
                    await guild.owner.send("I need the manage server permission to work properly.")
                except discord.errors.Forbidden:
                    print(f"Unable to send message to {guild.owner.name} in {guild.name}")
                pass

    async def user_expiration_update(self, userids):
        """updates entry time, if entry is expired this also removes it."""
        logging.debug(f"Checking all entries for expiration at {datetime.now()}")
        for guild in self.bot.guilds:
            for member in guild.members:
                await asyncio.sleep(0.1)
                if member.id not in userids:
                    logging.debug(f"User {member.id} not found in database, adding.")
                    UserTransactions.add_user_empty(member.id)
                    continue
                logging.debug(f"Updating entry time for {member.id}")
                UserTransactions.update_entry_date(member.id)

    async def user_expiration_remove(self, userdata, removaldate):
        """removes expired entries."""
        for entry in userdata:
            if entry.entry < removaldate:
                await asyncio.sleep(0.1)
                UserTransactions.user_delete(entry.uid)
                logging.debug(f"Database record: {entry.uid} expired")

    @tasks.loop(hours=48)
    async def check_users_expiration(self):
        """updates entry time, if entry is expired this also removes it."""
        if self.check_users_expiration.current_loop == 0:
            return
        print("checking user entries")
        userdata = UserTransactions.get_all_users()
        userids = [x.uid for x in userdata]
        removaldate = datetime.now() - timedelta(days=730)
        await self.user_expiration_update(userids)
        await self.user_expiration_remove(userdata, removaldate)
        print("Finished checking all entries")

    @tasks.loop(hours=12)
    async def check_active_servers(self):
        guild_ids = ServerTransactions().get_all()
        for guild in self.bot.guilds:
            if guild.id in guild_ids:
                guild_ids.remove(guild.id)
                continue
            ServerTransactions().add(guild.id, active=True)
        for gid in guild_ids:
            ServerTransactions().update(gid, active=False)



    @app_commands.command(name="expirecheck")
    @app_commands.checks.has_permissions(administrator=True)
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

    @check_active_servers.before_loop
    async def before_serverhcheck(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    """Adds the cog to the bot."""
    await bot.add_cog(Tasks(bot))
