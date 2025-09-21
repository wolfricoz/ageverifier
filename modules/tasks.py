"""This cogs handles all the tasks."""
import asyncio
import logging
import os
from datetime import datetime, timedelta

import discord
from discord_py_utilities.invites import check_guild_invites
from discord_py_utilities.messages import send_message, send_response
from discord import app_commands
from discord.ext import commands, tasks

from classes.AgeCalculations import AgeCalculations
from classes.access import AccessControl
from classes.ageroles import change_age_roles
from classes.encryption import Encryption
from classes.support.queue import Queue
from databases.controllers.ConfigData import ConfigData
from databases.controllers.DatabaseTransactions import DatabaseTransactions
from databases.controllers.ServerTransactions import ServerTransactions
from databases.controllers.UserTransactions import UserTransactions

OLDLOBBY = int(os.getenv("OLDLOBBY"))


class Tasks(commands.GroupCog) :
	def __init__(self, bot: commands.AutoShardedBot) :
		"""loads tasks"""
		self.bot = bot
		self.index = 0
		self.config_reload.start()
		self.check_users_expiration.start()
		self.check_active_servers.start()
		self.update_age_roles.start()
		self.database_ping.start()
		self.refresh_invites.start()

	def cog_unload(self) :
		"""unloads tasks"""
		self.config_reload.cancel()
		self.check_users_expiration.cancel()
		self.check_active_servers.cancel()
		self.update_age_roles.cancel()
		self.database_ping.cancel()
		self.refresh_invites.cancel()

	@tasks.loop(minutes=10)
	async def config_reload(self) :
		"""Reloads the config for the latest data."""
		AccessControl().reload()
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
			await asyncio.sleep(0.001)
			await self.update_user_time(member, userids)

	async def update_user_time(self, member, userids) :
		if member.id not in userids :
			logging.info(f"User {member.id} not found in database, adding.")
			UserTransactions().add_user_empty(member.id)
			return
		logging.debug(f"Updating entry time for {member.id}")
		UserTransactions().update_entry_date(member.id)

	async def user_expiration_remove(self, userdata) :
		"""removes expired entries."""
		for entry in userdata :
			await asyncio.sleep(0.001)
			await self.expiration_check(entry)

	async def expiration_check(self, entry) :
		if entry.entry < datetime.now(entry.entry.tzinfo) - timedelta(days=365) :
			UserTransactions().permanent_delete(entry.uid, "Expiration Check (Entry Expired)")
			# logging.info("DEV: EXPIRATION CHECK DISABLED")
			logging.info(f"Database record: {entry.uid} expired with date: {entry.entry}")
		if entry.deleted_at and entry.deleted_at < datetime.now() - timedelta(days=30) :
			UserTransactions().permanent_delete(entry.uid, "GDPR Removal (30 days passed)")
			# logging.info("DEV: EXPIRATION CHECK DISABLED")
			logging.info(f"Database record: {entry.uid} GDPR deleted with date: {entry.deleted_at}")

	@tasks.loop(hours=12)
	async def check_users_expiration(self) :
		"""updates entry time, if entry is expired this also removes it."""
		logging.info("Checking for expired entries.")
		userdata = UserTransactions().get_all_users()
		userids = [x.uid for x in userdata]
		await self.user_expiration_update(userids)
		await self.user_expiration_remove(userdata)
		logging.info("Finished checking all entries")

	@tasks.loop(minutes=10)
	async def refresh_invites(self):
		self.bot.invites = {}
		for guild in self.bot.guilds :
			self.bot.invites[guild.id] = await guild.invites()

	@tasks.loop(hours=12)
	async def check_active_servers(self) :
		guild_ids = ServerTransactions().get_all()
		for guild in self.bot.guilds :
			if guild.id in guild_ids :
				guild_ids.remove(guild.id)
				continue
			ServerTransactions().add(guild.id,
			                         active=True,
			                         name=guild.name,
			                         owner=guild.owner,
			                         member_count=guild.member_count,
			                         invite=await check_guild_invites(self.bot, guild)
			                         )

		for gid in guild_ids :
			try:
				guild = self.bot.get_guild(gid)
				if guild is None:
					guild = await self.bot.fetch_guild(gid)
			except discord.errors.NotFound:
				ServerTransactions().delete(gid)
				continue
			ServerTransactions().add(gid,
			                         active=False,
			                         name=guild.name,
			                         owner=guild.owner,
			                         member_count=guild.member_count,
			                         invite=await check_guild_invites(self.bot, guild)
			                         )
		ConfigData().reload()

	@tasks.loop(hours=24 * 7)
	async def update_age_roles(self) :
		logging.info("Updating age roles.")
		if self.update_age_roles.current_loop == 0 :
			logging.info("Skipping age role update on startup.")
			return
		for guild in self.bot.guilds :
			await asyncio.sleep(0.001)
			rem_roles = (ConfigData().get_key_or_none(guild.id, "REM") or []) + (
						ConfigData().get_key_or_none(guild.id, "JOIN") or [])
			mod_lobby = guild.get_channel(ConfigData().get_key_int_or_zero(guild.id, "lobbymod"))
			if mod_lobby is None :
				logging.info(f"Mod lobby not found in {guild.name}, skipping age role update.")
				continue
			if not rem_roles :
				Queue().add(send_message(mod_lobby,
				                         f"Your server does not have any removal roles or on join roles setup, because of this automatic age role updates are disabled to prevent users in the lobby from getting age roles."),
				            priority=0)
				return
			if ConfigData().get_key_or_none(guild.id, "UPDATEROLES") != "ENABLED" :
				logging.info(f"Skipping {guild.name} age role update.")
				continue
			for member in guild.members :
				try :
					member_data = UserTransactions().get_user(member.id)
					if member_data is None or member_data.date_of_birth is None :
						continue
					date_of_birth = Encryption().decrypt(member_data.date_of_birth)
					if "-" in date_of_birth :
						date_of_birth = date_of_birth.replace("-", "/")
						UserTransactions().update_user_dob(member.id, date_of_birth, guild.name)
					age = AgeCalculations.dob_to_age(date_of_birth)
					user_roles = [role.id for role in member.roles]


					for rem_role in rem_roles :
						if rem_role in user_roles :
							logging.info(f"User {member.name} still in the lobby")
							continue
					Queue().add(change_age_roles(guild, member, age, remove=True), priority=0)
				except Exception as e :
					logging.error(f"Error calculating age for {member.name}: {e}", exc_info=True)
					continue

	@tasks.loop(minutes=1)
	async def database_ping(self) :
		"""pings the database to keep the connection alive"""
		logging.debug("Pinging database.")
		DatabaseTransactions().ping_db()


	@app_commands.command(name="expirecheck")
	@app_commands.checks.has_permissions(administrator=True)
	async def expirecheck(self, interaction: discord.Interaction) :
		"""forces the automatic search ban check to start; normally runs every 30 minutes"""
		await send_response(interaction, "[Debug]Checking all entries.")
		self.check_users_expiration.restart()
		await interaction.followup.send("check-up finished.")

	@update_age_roles.before_loop
	async def before_update_age_roles(self) :
		"""stops event from starting before the bot has fully loaded"""
		await self.bot.wait_until_ready()

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

	@database_ping.before_loop
	async def before_ping(self) :
		"""stops event from starting before the bot has fully loaded"""
		await self.bot.wait_until_ready()

async def setup(bot) :
	"""Adds the cog to the bot."""
	await bot.add_cog(Tasks(bot))
