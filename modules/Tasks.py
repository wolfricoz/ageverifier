"""This cogs handles all the tasks."""
import asyncio
import logging
import os
from datetime import UTC, datetime, timedelta

import discord
from discord import app_commands
from discord.ext import commands, tasks
from discord_py_utilities.invites import check_guild_invites
from discord_py_utilities.messages import send_message, send_response

from classes.AgeCalculations import AgeCalculations
from classes.access import AccessControl
from classes.ageroles import change_age_roles
from classes.dashboard.Servers import Servers
from classes.encryption import Encryption
from classes.support.queue import Queue
from databases.current import Servers as servers_DB
from databases.transactions.ConfigData import ConfigData
from databases.transactions.ServerTransactions import ServerTransactions
from databases.transactions.UserTransactions import UserTransactions

OLDLOBBY = int(os.getenv("OLDLOBBY"))
DEBUG = os.getenv("DEBUG")


class Tasks(commands.Cog) :
	"""
	This is the bot's engine room! This module handles all the automated, behind-the-scenes tasks that keep everything running smoothly.
	You'll find tasks for cleaning up old messages, updating user data, refreshing server configurations, and much more.
	Most of these functions run on a schedule and don't require any user interaction.
	There is one command available for administrators to manually trigger a specific task.
	"""
	def __init__(self, bot: commands.AutoShardedBot) :
		"""loads tasks"""
		self.bot = bot
		self.index = 0
		self.config_reload.start()
		self.check_users_expiration.start()
		self.check_active_servers.start()
		self.update_age_roles.start()
		# self.database_ping.start()
		self.refresh_invites.start()
		self.clean_guilds.start()

	def cog_unload(self) :
		"""unloads tasks"""
		self.config_reload.cancel()
		self.check_users_expiration.cancel()
		self.check_active_servers.cancel()
		self.update_age_roles.cancel()
		# self.database_ping.cancel()
		self.refresh_invites.cancel()
		self.clean_guilds.cancel()


	@tasks.loop(minutes=10)
	async def config_reload(self) :
		"""Reloads the config for the latest data."""
		# Storing old config for debugging
		ConfigData().output_to_json()
		ConfigData().cleanup()
		AccessControl().reload()
		print("config reload")
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

	async def clean_lobby(self, guild: discord.Guild) :
		# Setup for the function; preparing the variables.
		logging.info(f"cleaning lobby for {guild.name}")
		count_messages = 0
		kicked_users = []
		lobby_channel = guild.get_channel(ConfigData().get_key_int_or_zero(guild.id, "server_join_channel"))
		mod_lobby = guild.get_channel(ConfigData().get_key_int_or_zero(guild.id, "approval_channel"))
		days = ConfigData().get_key_int_or_zero(guild.id, "clean_lobby_days")
		guild_db: servers_DB = ServerTransactions().get(guild.id)
		removal_message = (
			f"You have been removed from the server due to {days} days of inactivity. "
			f"If you’d like to rejoin, you’re always welcome back! Here’s a new invite link: {guild_db.invite}"
		)

		if not lobby_channel :
			logging.warning(f"[clean-up] No lobby channel found for {guild.name}")
			return
		if days == 0:
			logging.info(f"[clean-up] Days are set to 0, skipping {guild.name}")
			return
		removal_date = datetime.now(tz=UTC) - timedelta(days=days)

		async for message in lobby_channel.history(limit=None, before=removal_date):
			logging.debug(f"Message: {message.content}")
			if message.author != self.bot.user:
				Queue().add(message.delete(), 0)
				count_messages += 1
			if message.author.guild_permissions.manage_messages:
				continue
			if message.author != self.bot.user or len(message.mentions) < 1:
				continue
			user = message.mentions[0]

			if user.guild_permissions.manage_messages :
				continue
			count_messages +=1
			if user.global_name not in kicked_users :
				kicked_users.append(user.global_name)
			if not DEBUG:
				Queue().add(user.send(removal_message), 0)
				Queue().add(user.kick(reason=f"In lobby for more than {days} days"),0)
				Queue().add(message.delete(),0)
		if count_messages < 1 and len(kicked_users) < 1 :
			return

		if not os.path.isdir('temp') :
			os.mkdir('temp')


		with open("temp/kicked.txt", "w") as file :
			str_kicked = "\n".join(kicked_users)
			file.write("These users were queue'd for removal during the purge:\n")
			file.write(str_kicked)
		await mod_lobby.send(
			f"[Automatic Lobby Cleanup] cleaned up {len(kicked_users)} users and {count_messages} messages",
			file=discord.File(file.name, "autocleanup.txt")
		)
		os.remove("temp/kicked.txt")



	@tasks.loop(hours=24)
	async def clean_guilds(self) :
		"""This function cleans up the guilds from left-over messages, and inactive users"""
		await asyncio.sleep(15)
		logging.info("Cleaning up guilds.")
		access_control = AccessControl()
		if len(access_control.premium_guilds) < 1:
			access_control.add_premium_guilds_to_list()
		premium_guilds = access_control.premium_guilds
		for gid in premium_guilds:
			guild = self.bot.get_guild(gid)
			if not guild :
				continue
			Queue().add(self.clean_lobby(guild))

	@tasks.loop(minutes=10)
	async def refresh_invites(self) :
		self.bot.invites = {}
		for guild in self.bot.guilds :
			try:
				self.bot.invites[guild.id] = await guild.invites()
			except Exception as e :
				logging.warning(f"Could not refresh invites for {guild.name}: {e}")
				continue

	@tasks.loop(minutes=30)
	async def check_active_servers(self) :
		guild_ids = ServerTransactions().get_all()
		count = 0
		for guild in self.bot.guilds :
			if count % 10 == 0 :
				logging.info(f"updating active servers: processed {count} guilds so far.")
				await asyncio.sleep(0)

			if guild.id in guild_ids :
				guild_ids.remove(guild.id)
				count += 1
				continue
			try:
				ServerTransactions().add(guild.id,
				                         active=True,
				                         name=guild.name,
				                         owner=guild.owner,
				                         member_count=guild.member_count,
				                         invite=await check_guild_invites(self.bot, guild)
				                         )
				count += 1
			except:
				logging.error(f"Error adding guild {guild.name} ({guild.id}) to the database", exc_info=True)
				count += 1
				continue



		for gid in guild_ids :
			try :
				guild = self.bot.get_guild(gid)
				if guild is None :
					guild = await self.bot.fetch_guild(gid)
			except discord.errors.NotFound :
				ServerTransactions().delete(gid)
				continue
			ServerTransactions().add(gid,
			                         active=False,
			                         name=guild.name,
			                         owner=guild.owner,
			                         member_count=guild.member_count,
			                         invite=await check_guild_invites(self.bot, guild)
			                         )

		guilds = ServerTransactions().get_all(id_only=False)
		for guild in guilds :
			Queue().add(Servers().update_server(guild), 0)

	@tasks.loop(hours=24 * 7)
	async def update_age_roles(self) :
		logging.info("Updating age roles.")
		if self.update_age_roles.current_loop == 0 :
			logging.info("Skipping age role update on startup.")
			return
		for guild in self.bot.guilds :
			await asyncio.sleep(0.001)
			rem_roles = (ConfigData().get_key_or_none(guild.id, "verification_remove_role") or []) + (
					ConfigData().get_key_or_none(guild.id, "server_join_role") or [])
			mod_lobby = guild.get_channel(ConfigData().get_key_int_or_zero(guild.id, "approval_channel"))
			if mod_lobby is None :
				logging.info(f"Mod lobby not found in {guild.name}, skipping age role update.")
				continue
			if not rem_roles :
				Queue().add(send_message(mod_lobby,
				                         f"Your server does not have any removal roles or on join roles setup, because of this automatic age role updates are disabled to prevent users in the lobby from getting age roles."),
				            priority=0)
				return
			if ConfigData().get_key_or_none(guild.id, "auto_update_age_roles") != "ENABLED" :
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

	# Disabled, since the status page pings the bot every 5 minutes anyway.
	# @tasks.loop(minutes=1)
	# async def database_ping(self) :
	# 	"""pings the database to keep the connection alive"""
	# 	logging.debug("Pinging database.")
	# 	DatabaseTransactions().ping_db()

	@app_commands.command(name="expirecheck")
	@app_commands.checks.has_permissions(administrator=True)
	async def expirecheck(self, interaction: discord.Interaction) :
		"""
		This command allows an administrator to manually start the process of checking for expired user data.
		Normally, this check runs automatically every 12 hours. This is useful if you want to force an immediate data cleanup.
		You must have Administrator permissions to use this command.
		"""
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

	# @database_ping.before_loop
	# async def before_ping(self) :
	# 	"""stops event from starting before the bot has fully loaded"""
	# 	await self.bot.wait_until_ready()

	@clean_guilds.before_loop
	async def before_cleanup(self) :
		"""stops event from starting before the bot has fully loaded"""
		await self.bot.wait_until_ready()



async def setup(bot) :
	"""Adds the cog to the bot."""
	await bot.add_cog(Tasks(bot))
