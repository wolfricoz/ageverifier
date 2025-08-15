"""Config options for the bot."""
import asyncio
import logging
import os
import random
import re
from datetime import datetime, timedelta

from discord import app_commands
from discord.ext import commands
from discord_py_utilities.messages import send_message

from classes.jsonmaker import Configer
from classes.support.queue import Queue
from databases.Generators.uidgenerator import uidgenerator
from databases.controllers.ConfigData import ConfigData
from databases.controllers.HistoryTransactions import JoinHistoryTransactions
from databases.controllers.ServerTransactions import ServerTransactions
from databases.controllers.UserTransactions import UserTransactions
from databases.current import Users
from databases.enums.joinhistorystatus import JoinHistoryStatus
from views.modals.inputmodal import send_modal
from views.select.configselectroles import *
from discord_py_utilities.invites import check_guild_invites


def check_access() :
	def pred(interaction: discord.Interaction) -> bool :
		if interaction.user.id == int(os.getenv('DEVELOPER')) :
			return True
		return False

	return app_commands.check(pred)


class dev(commands.GroupCog, name="dev") :

	def __init__(self, bot: commands.Bot) :
		self.bot = bot

	async def create_invite(self, guild: discord.Guild) :
		try :
			config = ConfigData().get_key_int(guild.id, "lobbymod")
			invite = await guild.get_channel(config).create_invite(max_age=604800)
		except discord.Forbidden :
			invite = 'No permission'
		except Exception as e :
			invite = f'No permission/Error'
			logging.error(f"Error creating invite: {e}")
		return invite

	@app_commands.command(name="announce", description="[DEV] Send an announcement to all guild owners")
	@check_access()
	async def announce(self, interaction: discord.Interaction) :
		if interaction.user.id != int(os.getenv('DEVELOPER')) :
			await send_response(interaction, "You are not a developer", ephemeral=True)
			return
		message = await send_modal(interaction, "What is the announcement?", "Announcement", 1700)
		bot = self.bot
		supportguild = bot.get_guild(int(os.getenv('SUPPORTGUILD')))
		support_invite = await self.create_invite(supportguild)
		announcement = (f"## AGE VERIFIER ANNOUNCEMENT"
		                f"\n{message}"
		                f"\n-# You can join our support server by [clicking here to join]({support_invite}). If you have any questions, errors or concerns, please open a ticket in the support server.")

		for guild in self.bot.guilds :
			await asyncio.sleep(1)
			try :
				configid = ConfigData().get_key_int(guild.id, "lobbymod")
				channel = self.bot.get_channel(configid)
				await channel.send(announcement)
			except Exception as e :
				try :
					await guild.owner.send(
						f"Age Verifier could not send the announcement to your lobbymod in {guild.name}, please check the mod channel settings. You can setup your lobbymod with: ```/config channels key:lobbymod action:set value:```")
					await guild.owner.send(announcement)
				except Exception as e :
					await interaction.channel.send(f"Error sending to {guild}({guild.owner}): {e}")

	@app_commands.command(name="servers", description="[DEV] Send an announcement to all guild owners")
	@check_access()
	async def show_servers(self, interaction: discord.Interaction) :
		if interaction.user.id != int(os.getenv('DEVELOPER')) :
			await send_response(interaction, "You are not a developer", ephemeral=True)
			return
		servers = []
		for guild in self.bot.guilds :
			guild_info = f"name: {guild.name}({guild.id}) Owner: {guild.owner}({guild.owner.id}) User count: {len(guild.members)}"
			servers.append(guild_info)
		server_message = "\n".join(servers)
		await send_message(interaction.channel, server_message)

	@app_commands.command(name="fill_queue")
	@check_access()
	async def fill_queue(self, interaction: discord.Interaction):
		await send_response(interaction, "Starting to fill the queue")
		count = 1
		async def test(c):
			logging.info(f"this is task: {c}")

		while count < 1000:
			Queue().add(test(count), priority=0)
			count += 1
		await send_message(interaction.channel, f"Filled the queue with {count} tasks")


	@app_commands.command(name="test_invite")
	@check_access()
	async def test_invite(self, interaction: discord.Interaction, invite: str) -> None:
		result = await check_guild_invites(self.bot, interaction.guild, invite)
		await send_response(interaction, "Result: " + str(result))

	@app_commands.command(name="create_stats")
	@check_access()
	async def test_stats(self, interaction: discord.Interaction, amount: int) -> None:
		count = 0

		while count < amount:
			JoinHistoryTransactions().add(uidgenerator().create(), 1022307023527890974, random.choice(list(JoinHistoryStatus)), created_at=datetime.now() - timedelta(days=round(count / 2)+3))
			count += 1
		await send_response(interaction, "Finished generating records")

	@app_commands.command(name="import_origin")
	@check_access()
	async def origin(self, interaction: discord.Interaction, create_records: bool = False) :
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
				lobbylog = ConfigData().get_key_or_none(guild.id, "lobbylog")
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
		guildid = int(guildid)
		await Configer.remove_from_blacklist(guildid)
		await send_response(interaction, f"Unblacklisted {guildid}")

	# blacklist user goes here
	@app_commands.command(name="blacklist_user", description="[DEV] Blacklist a user")
	@check_access()
	async def blacklist_user(self, interaction: discord.Interaction, userid: str) :
		userid = int(userid)
		await Configer.add_to_user_blacklist(userid)
		await send_response(interaction, f"Blacklisted {userid}")

	@app_commands.command(name="unblacklist_user", description="[DEV] Remove a user from the blacklist")
	@check_access()
	async def unblacklist_user(self, interaction: discord.Interaction, userid: str) :
		userid = int(userid)
		await Configer.remove_from_user_blacklist(userid)
		await send_response(interaction, f"Unblacklisted {userid}")

	@app_commands.command(name="server_info", description="[DEV] Checks server info")
	@check_access()
	async def serverinfo(self, interaction: discord.Interaction, server: str) :
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
	await bot.add_cog(dev(bot))
