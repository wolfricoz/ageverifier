"""This cogs handles all the tasks."""
import asyncio
import logging
import os
from datetime import datetime, time, timezone

import discord
from discord import app_commands
from discord.ext import commands, tasks
from discord_py_utilities.invites import check_guild_invites
from discord_py_utilities.messages import send_message, send_response

from classes.AgeCalculations import AgeCalculations
from classes.access import AccessControl
from classes.ageroles import change_age_roles
from classes.blacklist import blacklist_check
from classes.dashboard.Servers import Servers
from classes.encryption import Encryption
from classes.lobby.Clean import clean_lobby
from classes.permissions_notice import PermissionNotice
from classes.support.RetentionPolicy import enforce_data_retention_policy
from classes.support import quickleaves, weeklyreport
from classes.support.queue import Queue
from classes.verification.reminders import send_abandoned_reminders
from databases.transactions.ConfigData import ConfigData
from databases.transactions.ServerTransactions import ServerTransactions
from databases.transactions.UserTransactions import UserTransactions
from modules.DevTools import check_access
from resources.data.config_variables import WEEKLY_REPORT_HOUR

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
		self.sync_configs.start()
		self.update_age_roles.start()
		# self.database_ping.start()
		self.refresh_invites.start()
		self.clean_guilds.start()
		self.anonymize_data.start()
		self.update_invites.start()
		self.verification_reminders.start()
		self.weekly_report.start()


	def cog_unload(self) :
		"""unloads tasks"""
		self.config_reload.cancel()
		self.check_users_expiration.cancel()
		self.check_active_servers.cancel()
		self.sync_configs.cancel()
		self.update_age_roles.cancel()
		# self.database_ping.cancel()
		self.refresh_invites.cancel()
		self.clean_guilds.cancel()
		self.anonymize_data.cancel()
		self.update_invites.cancel()
		self.verification_reminders.cancel()
		self.weekly_report.cancel()

	@tasks.loop(minutes=10)
	async def config_reload(self) :
		"""Reloads the config for the latest data."""
		# Storing old config for debugging
		ConfigData().output_to_json()
		ConfigData().cleanup()
		AccessControl().reload()
		for guild in self.bot.guilds :
			try :
				self.bot.invites[guild.id] = await guild.invites()
			except discord.errors.Forbidden :
				print(f"Unable to get invites for {guild.name}")
				# Names the server + how to fix, instead of a context-free owner DM.
				await PermissionNotice.notify(guild, missing=["manage_guild"],
				                              purpose="read invite data for invite tracking")

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

	async def user_expiration_remove(self) :
		"""removes expired entries."""

		await self.dob_expiration_check()
		await self.clean_deleted_users()

	@staticmethod
	async def purge_record(userid, reason: str) :
		"""
		Permanently deletes one user without blocking the event loop.
		"""
		await asyncio.to_thread(UserTransactions().permanent_delete, userid, reason)

	async def dob_expiration_check(self) :
		"""
		removes expired entries based on dob expiration
		:return:
		"""
		records = UserTransactions().get_all_expired()
		count = 0
		for entry in records :
			if count % 10 == 0 :
				logging.info(f"Processed {count} expired entries so far.")
				await asyncio.sleep(0)
			await self.purge_record(entry[0], "Expiration Check (Entry Expired)")
			# logging.info("DEV: EXPIRATION CHECK DISABLED")
			logging.info(f"Database record: {entry[0]} expired with date: {entry[1]}")
			count += 1
		logging.info(f"Finished checking all expired entries, total removed: {count}")

	async def clean_deleted_users(self) :
		"""
		removes expired entries based on GDPR deletion expiration
		:return:
		"""
		records = UserTransactions().get_all_soft_deleted(expired=True)
		count = 0
		for entry in records :
			if count % 10 == 0 :
				logging.info(f"Processed {count} GDPR expired entries so far.")
			# The delete and the increment used to sit inside the modulo guard above, so
			# count stuck at 1 after the first record and the guard never matched again -
			# every remaining entry was skipped and the GDPR purge silently did nothing.
			await self.purge_record(entry, "GDPR Removal (30 days passed)")
			count += 1
		logging.info(f"Finished checking all GDPR expired entries, total removed: {count}")

	@tasks.loop(hours=12)
	async def check_users_expiration(self) :
		"""updates entry time, if entry is expired this also removes it."""
		logging.info("Checking for expired entries.")
		userdata = UserTransactions().get_all_users()
		userids = [x.uid for x in userdata]
		await self.user_expiration_update(userids)
		await self.user_expiration_remove()
		logging.info("Finished checking all entries")

	@tasks.loop(hours=24)
	async def clean_guilds(self) :
		"""This function cleans up the guilds from left-over messages, and inactive users"""
		await asyncio.sleep(15)
		logging.info("Cleaning up guilds.")
		access_control = AccessControl()
		if len(access_control.premium_guilds) < 1 :
			access_control.add_premium_guilds_to_list()
		premium_guilds = access_control.premium_guilds
		for gid in premium_guilds :
			guild = self.bot.get_guild(gid)
			if not guild :
				continue
			kick = ConfigData().get_toggle(guild.id, "KICK_ON_CLEAN")

			Queue().add(clean_lobby(self.bot, guild, kick=kick))

	@tasks.loop(minutes=10)
	async def refresh_invites(self) :
		self.bot.invites = {}
		for guild in self.bot.guilds :
			try :
				self.bot.invites[guild.id] = await guild.invites()
			except Exception as e :
				logging.warning(f"Could not refresh invites for {guild.name}: {e}")
				continue

	@tasks.loop(hours=1)
	async def check_active_servers(self) :
		"""Keeps the servers table in sync with the guilds the bot is in.

		Only lightweight server state is touched here (active / name / owner /
		member_count). Config defaults are seeded once for brand-new guilds by
		ServerTransactions.add(); backfilling newly-introduced config keys to
		existing guilds is handled separately by the daily sync_configs task.
		"""
		db_ids = set(await asyncio.to_thread(ServerTransactions().get_all))
		live_ids = {guild.id for guild in self.bot.guilds}

		new_ids = live_ids - db_ids          # guilds we don't have a row for yet
		removed_ids = db_ids - live_ids      # rows for guilds we're no longer in

		count = 0
		total = len(self.bot.guilds)

		devroom = self.bot.get_channel(self.bot.DEV)
		for guild in self.bot.guilds :
			await blacklist_check(guild, devroom)
			await asyncio.sleep(0)
			if count % 10 == 0 :
				logging.info(f"updating active servers: processed {count}/{total} guilds so far.")
			count += 1

			try :
				if guild.id in new_ids :
					# Brand-new server: full add() also seeds its default config.
					await asyncio.to_thread(ServerTransactions().add, guild.id,
					                        active=True,
					                        name=guild.name,
					                        owner=guild.owner,
					                        member_count=guild.member_count,
					                        reload=False,
					                        )
				else :
					# Existing server: lightweight state refresh only, no config churn.
					await asyncio.to_thread(ServerTransactions().update, guild.id,
					                        active=True,
					                        name=guild.name,
					                        owner=guild.owner.name if guild.owner else 'unknown',
					                        member_count=guild.member_count,
					                        owner_id=guild.owner_id if guild.owner_id else 0,
					                        reload=False,
					                        )
			except Exception as e :
				logging.exception(f"Error syncing guild {guild.name} ({guild.id}) to the database: error: {e}")
				continue

		# Deactivate (or delete) servers the bot is no longer a member of.
		logging.info(f"pending removal: {removed_ids}")
		for gid in removed_ids :
			try :
				guild = self.bot.get_guild(gid)
				if guild is None :
					guild = await self.bot.fetch_guild(gid)
			except discord.errors.NotFound :
				await asyncio.to_thread(ServerTransactions().delete, gid)
				continue
			await asyncio.to_thread(ServerTransactions().update, gid,
			                        active=False,
			                        name=guild.name,
			                        owner=guild.owner.name if guild.owner else None,
			                        member_count=guild.member_count,
			                        owner_id=guild.owner.id if guild.owner else None,
			                        reload=False,
			                        )

		guilds = await asyncio.to_thread(ServerTransactions().get_all, id_only=False)

		await asyncio.to_thread(Queue().add, Servers().update_servers(guilds), 0)
		await asyncio.sleep(0)

		AccessControl().reload()

	@tasks.loop(hours=24)
	async def sync_configs(self) :
		logging.info("Syncing config defaults across all guilds.")
		inserted = await asyncio.to_thread(ServerTransactions().backfill_config)
		if inserted :
			await ConfigData().load_all_guilds()
		logging.info(f"Config sync complete. Inserted {inserted} missing config rows.")

	@tasks.loop(hours=24 * 3)
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

	@tasks.loop(hours=24)
	async def anonymize_data(self) :
		logging.info("Starting data anonymization.")
		enforce_data_retention_policy()
		logging.info(f"Deleted {await asyncio.to_thread(quickleaves.prune)} expired quick leave files.")
		logging.info("Data anonymized.")

	@tasks.loop(hours=12)
	async def update_invites(self) :
		if self.update_invites.current_loop == 0 :
			logging.info("Skipping invite update on startup.")
			return
		servers = ServerTransactions().get_invalid_invites()
		if not servers :
			logging.info("No invites to updates.")
			return
		server_count = len(servers)
		count = 0
		for server in servers :
			if count % 10 == 0 :
				logging.info(f"Updating {count}/{server_count} servers.")
				await asyncio.sleep(0)
			# Servers is keyed on `guild`; it has no `id` column (AGEVERIFIER-FQ).
			guild = self.bot.get_guild(server.guild)
			if guild is None :
				continue
			invite = await check_guild_invites(self.bot, guild, server.invite)
			ServerTransactions().update(server.guild, invite=invite, invite_date=datetime.now())
			count += 1
		logging.info(f"Updated {count}/{server_count} servers.")


	@tasks.loop(minutes=5)
	async def verification_reminders(self) :
		"""Reminds members who opened the online verification page but did not finish it."""
		try :
			await send_abandoned_reminders(self.bot)
		except Exception as e :
			# A failing run must not stop the loop; the next run picks the same links up again.
			logging.error(f"Abandoned verification reminders failed: {e}", exc_info=True)

	@tasks.loop(time=time(hour=WEEKLY_REPORT_HOUR, tzinfo=timezone.utc))
	async def weekly_report(self) :
		"""Posts the weekly developer stats report to the DEV channel. Runs daily, only reports on Sundays."""
		if datetime.now(tz=timezone.utc).weekday() != 6 :
			return
		try :
			await weeklyreport.send(self.bot)
		except Exception as e :
			# A failing report must not stop the loop; next Sunday tries again.
			logging.error(f"Weekly stats report failed: {e}", exc_info=True)

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

	@sync_configs.before_loop
	async def before_sync_configs(self) :
		await self.bot.wait_until_ready()

	# @database_ping.before_loop
	# async def before_ping(self) :
	# 	"""stops event from starting before the bot has fully loaded"""
	# 	await self.bot.wait_until_ready()

	@clean_guilds.before_loop
	async def before_cleanup(self) :
		"""stops event from starting before the bot has fully loaded"""
		await self.bot.wait_until_ready()

	@verification_reminders.before_loop
	async def before_verification_reminders(self) :
		await self.bot.wait_until_ready()

	@weekly_report.before_loop
	async def before_weekly_report(self) :
		await self.bot.wait_until_ready()

	@anonymize_data.before_loop
	async def before_dataanonymize(self) :
		"""stops event from starting before the bot has fully loaded"""
		await self.bot.wait_until_ready()

	@app_commands.command(name="sync_servers",
	                      description="[DEV] Forces all servers to be synced with the dashboard")
	@check_access()
	async def inspect_queue(self, interaction: discord.Interaction) :
		"""
		[DEV] Inspects the current state of the task queue for debugging.

		**Permissions:**
		- `Developer`
		"""
		await send_response(interaction, "[Debug]Checking all entries.")
		self.check_active_servers.restart()

	@app_commands.command(name="stats_report",
	                      description="[DEV] Posts the weekly stats report for the last 7 days to the dev channel now")
	@check_access()
	async def stats_report(self, interaction: discord.Interaction) :
		"""
		[DEV] Posts the weekly developer stats report now, covering the last 7 days, instead of waiting for Sunday.

		**Permissions:**
		- `Developer`
		"""
		await send_response(interaction, "Building the weekly stats report.", ephemeral=True)
		sent = await weeklyreport.send(self.bot)
		await interaction.followup.send("Report posted to the dev channel." if sent else
		                                "The report could not be posted, check the logs.", ephemeral=True)


async def setup(bot) :
	"""Adds the cog to the bot."""
	await bot.add_cog(Tasks(bot))
