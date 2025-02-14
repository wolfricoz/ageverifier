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
from classes.support.queue import queue

OLDLOBBY = int(os.getenv("OLDLOBBY"))


class Tasks(commands.GroupCog) :
	def __init__(self, bot) :
		"""loads tasks"""
		self.bot = bot
		self.index = 0
		self.config_reload.start()
		self.check_users_expiration.start()
		self.check_active_servers.start()

	def cog_unload(self) :
		"""unloads tasks"""
		self.config_reload.cancel()
		self.check_users_expiration.cancel()
		self.check_active_servers.cancel()

	@tasks.loop(hours=1)
	async def config_reload(self) :
		"""Reloads the config for the latest data."""
		for guild in self.bot.guilds :
			ConfigData().load_guild(guild.id)
		print("config reload")
		ConfigData().output_to_json()
		for guild in self.bot.guilds :
			try :
				self.bot.invites[guild.id] = await guild.invites()
			except discord.errors.Forbidden :
				print(f"Unable to get invites for {guild.name}")
				try :
					await guild.owner.send("I need the manage server permission to work properly.")
				except discord.errors.Forbidden :
					print(f"Unable to send message to {guild.owner.name} in {guild.name}")
				pass

	async def user_expiration_update(self, userids) :
		"""updates entry time, if entry is expired this also removes it."""
		logging.debug(f"Checking all entries for expiration at {datetime.now()}")
		# Making a list of all members and removing duplicates.
		members = list(set([member for guild in self.bot.guilds for member in guild.members]))
		for member in members :
			queue().add(self.update_user_time(member, userids), priority=0)

	async def update_user_time(self, member, userids, count, members) :
		if member.id not in userids :
			logging.info(f"User {member.id} not found in database, adding.")
			UserTransactions.add_user_empty(member.id)
			return
		logging.info(f"Updating entry time for {member.id}")
		UserTransactions.update_entry_date(member.id)

	async def user_expiration_remove(self, userdata, removaldate) :
		"""removes expired entries."""
		for entry in userdata :
			queue().add(self.expiration_check(entry), priority=0)

	async def expiration_check(self, entry) :
		if entry.entry < datetime.now() - timedelta(days=365) :
			UserTransactions.permanent_delete(entry.uid, "Expiration Check (Entry Expired)")
			# logging.info("DEV: EXPIRATION CHECK DISABLED")
			logging.info(f"Database record: {entry.uid} expired with date: {entry.entry}")
		if entry.deleted_at and entry.deleted_at < datetime.now() - timedelta(days=30) :
			UserTransactions.permanent_delete(entry.uid, "GDPR Removal (30 days passed)")
			# logging.info("DEV: EXPIRATION CHECK DISABLED")
			logging.info(f"Database record: {entry.uid} GDPR deleted with date: {entry.deleted_at}")

	@tasks.loop(hours=12)
	async def check_users_expiration(self) :
		"""updates entry time, if entry is expired this also removes it."""
		logging.info("Checking for expired entries.")
		userdata = UserTransactions.get_all_users()
		userids = [x.uid for x in userdata]
		removaldate = datetime.now() - timedelta(days=730)
		queue().add(self.user_expiration_update(userids), priority=0)
		queue().add(self.user_expiration_remove(userdata, removaldate), priority=0)
		logging.info("Finished checking all entries")

	@tasks.loop(hours=12)
	async def check_active_servers(self) :
		guild_ids = ServerTransactions().get_all()
		for guild in self.bot.guilds :
			if guild.id in guild_ids :
				guild_ids.remove(guild.id)
				continue
			ServerTransactions().add(guild.id, active=True, reload=False)

		for gid in guild_ids :
			ServerTransactions().update(gid, active=False, reload=False)
		ConfigData().reload()

	@app_commands.command(name="expirecheck")
	@app_commands.checks.has_permissions(administrator=True)
	async def expirecheck(self, interaction: discord.Interaction) :
		"""forces the automatic search ban check to start; normally runs every 30 minutes"""
		await interaction.response.send_message("[Debug]Checking all entries.")
		self.check_users_expiration.restart()
		await interaction.followup.send("check-up finished.")

	@check_users_expiration.before_loop
	async def before_expire(self) :
		"""stops event from starting before the bot has fully loaded"""
		await self.bot.wait_until_ready()

	@config_reload.before_loop  # it's called before the actual task runs
	async def before_checkactiv(self) :
		"""stops event from starting before the bot has fully loaded"""
		await self.bot.wait_until_ready()

	@check_active_servers.before_loop
	async def before_serverhcheck(self) :
		await self.bot.wait_until_ready()


async def setup(bot) :
	"""Adds the cog to the bot."""
	await bot.add_cog(Tasks(bot))
