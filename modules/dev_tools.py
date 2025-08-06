"""Config options for the bot."""
import asyncio
import logging
import os
import re

from discord import app_commands
from discord.ext import commands
from discord_py_utilities.messages import send_message

from classes.jsonmaker import Configer
from classes.support.queue import Queue
from databases.controllers.ConfigData import ConfigData
from databases.controllers.UserTransactions import UserTransactions
from databases.current import Users
from views.modals.inputmodal import send_modal
from views.select.configselectroles import *


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
			await interaction.response.send_message("You are not a developer", ephemeral=True)
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
			await interaction.response.send_message("You are not a developer", ephemeral=True)
			return
		servers = []
		for guild in self.bot.guilds :
			guild_info = f"name: {guild.name}({guild.id}) Owner: {guild.owner}({guild.owner.id}) User count: {len(guild.members)}"
			servers.append(guild_info)
		server_message = "\n".join(servers)
		await send_message(interaction.channel, server_message)

	@app_commands.command(name="import_origin")
	@check_access()
	async def origin(self, interaction: discord.Interaction) :
		user: Users
		history = {}
		if interaction.user.id != 188647277181665280 :
			await send_response(interaction, "You are not the developer", ephemeral=True)
			return
		await send_response(interaction, "Attempting to find origin of date of birth")
		users = UserTransactions().get_all_users(dob_only=True)
		for guild in self.bot.guilds :
			try :
				lobbylog = ConfigData().get_key(guild.id, "lobbylog")
			except :
				continue
			channel = guild.get_channel(int(lobbylog))
			history[str(guild.id)] = {}
			async for message in channel.history(limit=10000) :
				match = re.search(r"UID:\s(\d+)", message.content)
				if match is None :
					continue
				history[str(guild.id)][str(match.group(1))] = message.id
		for user in users :
			if user.server is not None :
				continue
			Queue().add(self.search(user, history, interaction.channel), priority=0)

	async def search(self, user, history, channel) :
		for guild in self.bot.guilds :
			if str(guild.id) in history and str(user.uid) in history[str(guild.id)] :
				UserTransactions().update_user(user.uid, server=guild.name)
				logging.info(f"{user.uid}'s entry found in {guild.name}, database has been updated")

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
		await interaction.response.send_message(f"Blacklisted {guild}")

	@app_commands.command(name="unblacklist_server", description="[DEV] Remove a server from the blacklist")
	@check_access()
	async def unblacklist_server(self, interaction: discord.Interaction, guildid: str) :
		guildid = int(guildid)
		await Configer.remove_from_blacklist(guildid)
		await interaction.response.send_message(f"Unblacklisted {guildid}")

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
