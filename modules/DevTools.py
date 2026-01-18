"""Config options for the bot."""
import asyncio
import logging
import os
import random
import re
from datetime import datetime, timedelta

from discord import app_commands
from discord.ext import commands
from discord_py_utilities.invites import check_guild_invites, create_invite
from discord_py_utilities.messages import send_message
from discord_py_utilities.permissions import find_first_accessible_text_channel

from classes.jsonmaker import Configer
from classes.onboarding import Onboarding
from classes.support.queue import Queue
from databases.Generators.uidgenerator import uidgenerator
from databases.current import Users
from databases.enums.joinhistorystatus import JoinHistoryStatus
from databases.transactions.ConfigData import ConfigData
from databases.transactions.HistoryTransactions import JoinHistoryTransactions
from databases.transactions.ServerTransactions import ServerTransactions
from databases.transactions.UserTransactions import UserTransactions
from views.modals.inputmodal import send_modal
from views.select.configselectroles import *


def check_access() :
	def pred(interaction: discord.Interaction) -> bool :
		if interaction.user.id == int(os.getenv('DEVELOPER')) :
			return True
		return False

	return app_commands.check(pred)


class DevTools(commands.GroupCog, name="dev", description="A set of commands for bot developers to manage and diagnose the bot.") :
	"""
	A set of commands for bot developers to manage and diagnose the bot.
	These commands are powerful and restricted to maintain the bot's health and security.
	Access is limited to users with the developer ID configured in the bot's environment variables.
	"""

	def __init__(self, bot: commands.Bot) :
		self.bot = bot



	@app_commands.command(name="announce", description="[DEV] Send an announcement to all guild owners")
	@check_access()
	async def announce(self, interaction: discord.Interaction) :
		"""
        Sends a global announcement to all servers where the bot is present.
        This command will first try to send the message to the configured 'approval_channel'. If that fails, it will attempt to DM the server owner.
        This is a powerful tool for communicating important updates or maintenance notices.

        **Permissions:**
        - This is a developer-only command.
        """
		if interaction.user.id != int(os.getenv('DEVELOPER')) :
			await send_response(interaction, "You are not a developer", ephemeral=True)
			return
		message = await send_modal(interaction, "What is the announcement?", "Announcement", 1700)
		bot = self.bot
		supportguild = bot.get_guild(int(os.getenv('SUPPORTGUILD')))
		channel = find_first_accessible_text_channel(supportguild)
		support_invite = await create_invite(channel)
		announcement = (f"## AGE VERIFIER ANNOUNCEMENT"
		                f"\n{message}"
		                f"\n-# You can join our support server by [clicking here to join]({support_invite}). If you have any questions, errors or concerns, please open a ticket in the support server.")

		for guild in self.bot.guilds :
			await asyncio.sleep(1)
			try :
				configid = ConfigData().get_key_int(guild.id, "approval_channel")
				channel = self.bot.get_channel(configid)
				await channel.send(announcement)
			except Exception as e :
				try :
					await guild.owner.send(
						f"Age Verifier could not send the announcement to your lobbymod in {guild.name}, please check the mod channel settings. You can setup your lobbymod with: ```/config channels key:lobbymod action:set value:```")
					await guild.owner.send(announcement)
				except Exception as e :
					await interaction.channel.send(f"Error sending to {guild}({guild.owner}): {e}")

	@app_commands.command(name="servers", description="[DEV] Lists all the servers the bot is currently a member of.")
	@check_access()
	async def show_servers(self, interaction: discord.Interaction) :
		"""
        Lists all the servers (guilds) the bot is currently a member of.
        The list includes the server name, ID, owner's name and ID, and the total member count. This is useful for getting a quick overview of the bot's reach.

        **Permissions:**
        - This is a developer-only command.
        """
		if interaction.user.id != int(os.getenv('DEVELOPER')) :
			await send_response(interaction, "You are not a developer", ephemeral=True)
			return
		servers = []
		for guild in self.bot.guilds :
			guild_info = f"name: {guild.name}({guild.id}) Owner: {guild.owner}({guild.owner.id}) User count: {len(guild.members)}"
			servers.append(guild_info)
		server_message = "\n".join(servers)
		await send_message(interaction.channel, server_message)

	@app_commands.command(name="fill_queue", description="[DEV] A testing command to populate the bot's background task queue.")
	@check_access()
	async def fill_queue(self, interaction: discord.Interaction):
		"""
        A testing command to populate the bot's background task queue with a large number of simple tasks.
        This is used to stress-test the queueing system and ensure it can handle a heavy load without issues.

        **Permissions:**
        - This is a developer-only command.
        """
		await send_response(interaction, "Starting to fill the queue")
		count = 1
		async def test(c):
			logging.info(f"this is task: {c}")

		while count < 1000:
			Queue().add(test(count), priority=0)
			count += 1
		await send_message(interaction.channel, f"Filled the queue with {count} tasks")


	@app_commands.command(name="test_invite", description="[DEV] Checks the validity and information of a given Discord invite link.")
	@check_access()
	async def test_invite(self, interaction: discord.Interaction, invite: str) -> None:
		"""
        Checks the validity and information of a given Discord invite link within the context of the current server.
        This helps in diagnosing issues related to invites or checking where they lead.

        **Permissions:**
        - This is a developer-only command.
        """
		result = await check_guild_invites(self.bot, interaction.guild, invite)
		await send_response(interaction, "Result: " + str(result))

	@app_commands.command(name="create_stats", description="[DEV] Generates a specified amount of fake join history records.")
	@check_access()
	async def test_stats(self, interaction: discord.Interaction, amount: int) -> None:
		"""
        Generates a specified amount of fake join history records for testing purposes.
        This is useful for populating the database with data to test statistics-related features and performance.

        **Permissions:**
        - This is a developer-only command.
        """
		count = 0

		async def create_stat(count):
			return JoinHistoryTransactions().add(uidgenerator().create(), 1022307023527890974, random.choice(list(JoinHistoryStatus)), created_at=datetime.now() - timedelta(days=random.randint(1, 7)))
		while count < amount:
			Queue().add(create_stat(count), priority=0)
			count += 1
		await send_response(interaction, "Finished generating records")

	@app_commands.command(name="import_origin", description="[DEV] A data migration and analysis tool.")
	@check_access()
	async def origin(self, interaction: discord.Interaction, create_records: bool = False) :
		"""
        A data migration and analysis tool. It scans through server logs to find the original server (origin) where a user's date of birth was first recorded.
        It can also create historical join records from this data. This is a very intensive operation.

        **Permissions:**
        - This is a developer-only command.
        """
		user: Users
		if interaction.user.id != 188647277181665280 :
			await send_response(interaction, "You are not the developer", ephemeral=True)
			return
		await send_response(interaction, "Attempting to find origin of date of birth")
		users = UserTransactions().get_all_users(dob_only=True)
		logging.info(f"Queued {len(users)} users")
		for guild in self.bot.guilds :
			logging.info(f"Checking {guild.name}({guild.id}) for records")
			try :
				lobbylog = ConfigData().get_key_or_none(guild.id, "age_log")
			except :
				logging.warning(f"Could not find lobbylog for {guild.name}({guild.id})")
				continue
			if lobbylog is None :
				logging.warning(f"Could not find lobbylog for {guild.name}({guild.id})")
				continue
			channel = guild.get_channel(int(lobbylog))
			Queue().add(await self.history(channel, users, guild, create_records), priority=0)

		await send_message(interaction.channel, f"Queued {len(users)} users to be updated.")

	async def history(self, channel, users, guild, create_records) :
		async for message in channel.history(limit=None) :
			match = re.search(r"UID:\s(\d+)", message.content)
			if match is None :
				return
			user_id = int(match.group(1))
			user_ids = [int(user.uid) for user in users]
			if int(match.group(1)) in user_ids :
				user = UserTransactions().get_user(user_id)
				if user.server is None :
					UserTransactions().update_user(user.uid, server=guild.name)
					logging.info(f"{user.uid}'s entry found in {guild.name}, database has been updated")
				if create_records :
					JoinHistoryTransactions().add(user.uid,
					                              guild.id,
					                              JoinHistoryStatus.SUCCESS,
					                              message_id=message.id,
					                              verification_date=message.created_at)

	# async def search(self, user, history, create_records: bool) :
	# 	for guild in self.bot.guilds :
	# 		if str(guild.id) in history and str(user.uid) in history[str(guild.id)] :
	# 			if user.server is None :
	# 				UserTransactions().update_user(user.uid, server=guild.name)
	# 				logging.info(f"{user.uid}'s entry found in {guild.name}, database has been updated")
	#
	# 			if create_records:
	# 				logging.info(f"Creating entry log for {user.uid}'s entry found in {guild.name}, ")
	# 				JoinHistoryTransactions().add(user.uid, guild.id, JoinHistoryStatus.SUCCESS, message_id=history[str(guild.id)][str(user.uid)]["message_id"], verification_date=history[str(guild.id)][str(user.uid)]["date"])

	@app_commands.command(name="blacklist_server", description="[DEV] Blacklist a server")
	@check_access()
	async def blacklist_server(self, interaction: discord.Interaction, guildid: str) :
		"""
        Adds a server to the blacklist, preventing the bot from being used there.
        The bot will automatically leave the server after it has been blacklisted. This is a permanent measure for problematic servers.

        **Permissions:**
        - This is a developer-only command.
        """
		guildid = int(guildid)
		guild = self.bot.get_guild(guildid)
		await Configer.add_to_blacklist(guildid)
		try :
			await guild.leave()
		except :
			pass
		await send_response(interaction, f"Blacklisted {guild}")

	@app_commands.command(name="unblacklist_server", description="[DEV] Remove a server from the blacklist")
	@check_access()
	async def unblacklist_server(self, interaction: discord.Interaction, guildid: str) :
		"""
        Removes a server from the blacklist, allowing the bot to be invited back and used again.

        **Permissions:**
        - This is a developer-only command.
        """
		guildid = int(guildid)
		await Configer.remove_from_blacklist(guildid)
		await send_response(interaction, f"Unblacklisted {guildid}")

	# blacklist user goes here
	@app_commands.command(name="blacklist_user", description="[DEV] Blacklist a user")
	@check_access()
	async def blacklist_user(self, interaction: discord.Interaction, userid: str) :
		"""
        Adds a user to the blacklist, preventing them from interacting with the bot across all servers.
        This is a global ban from using the bot's services.

        **Permissions:**
        - This is a developer-only command.
        """
		userid = int(userid)
		await Configer.add_to_user_blacklist(userid)
		await send_response(interaction, f"Blacklisted {userid}")

	@app_commands.command(name="unblacklist_user", description="[DEV] Remove a user from the blacklist")
	@check_access()
	async def unblacklist_user(self, interaction: discord.Interaction, userid: str) :
		"""
        Removes a user from the global blacklist, allowing them to use the bot's services again.

        **Permissions:**
        - This is a developer-only command.
        """
		userid = int(userid)
		await Configer.remove_from_user_blacklist(userid)
		await send_response(interaction, f"Unblacklisted {userid}")

	@app_commands.command(name="server_info", description="[DEV] Checks server info")
	@check_access()
	async def serverinfo(self, interaction: discord.Interaction, server: str) :
		"""
        Retrieves and displays detailed information about a specific server.
        This includes owner, member counts, channel/role counts, creation date, and other useful metadata for support and diagnostics.

        This is used to review server details when needing to verify validity of the server, or get the invite link for support purposes. This is never to be shared outside of the support server.

        **Permissions:**
        - This is a developer-only command.
        """
		await send_response(interaction, "Retrieving server data")
		guild = self.bot.get_guild(int(server))
		if guild is None :
			guild = await self.bot.fetch_guild(int(server))
		if guild is None :
			return
		embed = discord.Embed(title=f"{guild.name}'s info")
		server_info = ServerTransactions().get(guild.id)
		guild_data = {
			"Owner"         : f"{guild.owner}({guild.owner.id})",
			"User count"    : len([m for m in guild.members if not m.bot]),
			"Bot count"     : len([m for m in guild.members if m.bot]),
			"Channel count" : len(guild.channels),
			"Role count"    : len(guild.roles),
			"Created at"    : guild.created_at.strftime("%m/%d/%Y"),
			"MFA level"     : guild.mfa_level,
			"invite"        : server_info.invite,
			"server ID"     : guild.id,

		}
		for key, value in guild_data.items() :
			embed.add_field(name=key, value=value, inline=False)
		embed.set_footer(text=f"This data should not be shared outside of the support server.")
		await send_message(interaction.channel, embed=embed)

	@app_commands.command(name="test_start_onboarding", description="[DEV] Test start onboarding for server")
	@check_access()
	async def test_start_onboarding(self, interaction: discord.Interaction) :
		await Onboarding().join_message(interaction.channel)


# @app_commands.command(name="migrate", description="Migrates data")
# async def test(self, interaction: discord.Interaction):
# 	await send_response(interaction, f"Migrating IDverification table...")
# 	VerificationTransactions().migrate()
# 	await send_message(interaction.channel, f"Migrated IDverification table")

# @app_commands.command(name="add_staff", description="[DEV] Adds a staff member to the team")
# @app_commands.choices(role=[Choice(name=x, value=x.lower()) for x in ["Dev", "Rep"]])
# async def add_staff(self, interaction: discord.Interaction, user: discord.User, role: Choice[str]) :
# 	if interaction.user.id != int(os.getenv("OWNER")) :
# 		return await send_response(interaction, "You do not have permission to add staff members")
# 	StaffDbTransactions.add(user.id, role.value)
# 	await send_response(interaction, f"Staff member {user.mention} successfully added as a `{role.name}`!")
# 	AccessControl().reload()
#
# @app_commands.command(name="remove_staff", description="[DEV] Remove a staff member from the team")
# @AccessControl().check_access("dev")
# async def remove_staff(self, interaction: discord.Interaction, user: discord.User) :
# 	StaffDbTransactions.delete(user.id)
# 	await send_response(interaction, f"Staff member {user.mention} successfully removed!")
# 	AccessControl().reload()




async def setup(bot: commands.Bot) :
	"""Adds the cog to the bot"""
	await bot.add_cog(DevTools(bot))
