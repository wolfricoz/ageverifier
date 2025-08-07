"""this module handles the lobby."""
import datetime
import logging
import os
from datetime import datetime, timedelta

import discord
from discord import app_commands
from discord.ext import commands
from discord_py_utilities.messages import send_response

import classes.permissions as permissions
from classes.AgeCalculations import AgeCalculations
from classes.encryption import Encryption
from classes.lobbyprocess import LobbyProcess
from classes.whitelist import check_whitelist
from databases.controllers.ServerTransactions import ServerTransactions
from databases.controllers.UserTransactions import UserTransactions
from databases.controllers.VerificationTransactions import VerificationTransactions
from databases.current import Users
from resources.data.responses import StringStorage
from views.buttons.approvalbuttons import ApprovalButtons
from views.buttons.dobentrybutton import dobentry
from views.buttons.verifybutton import VerifyButton


class Database(commands.GroupCog) :
	def __init__(self, bot: commands.Bot) :
		self.bot = bot
		self.index = 0
		self.bot.add_view(VerifyButton())
		self.bot.add_view(ApprovalButtons())
		self.bot.add_view(dobentry())

	#     @app_commands.choices(operation=[Choice(name=x, value=x) for x in
	#                                      ['add', 'update', 'delete', 'get']])
	async def whitelist(self, interaction) :
		if not check_whitelist(interaction.guild.id) and not permissions.check_dev(interaction.user.id) :
			logging.info('not whitelisted')
			await send_response(interaction,
			                    f"[NOT_WHITELISTED] This command is limited to whitelisted servers. Please join our [support server]({os.getenv('INVITE')}) and open a ticket to edit or send a message to `ricostryker`")
			return True
		logging.info('whitelisted')
		return False

	@app_commands.command()
	@app_commands.checks.has_permissions(manage_messages=True)
	async def stats(self, interaction: discord.Interaction) :
		records = UserTransactions().get_all_users()
		servers = ServerTransactions().get_all(id_only=False)
		verifications = VerificationTransactions().get_all()
		data = {
			"Records"               : len(records),
			"Records with Dobs"     : len([record for record in records if record.date_of_birth is not None]),
			"Expired records"       : len(
				[record for record in records if record.entry < datetime.now() - timedelta(days=365)]),
			"Records with IDchecks" : len([verification for verification in verifications if verification.idcheck is True]),
			"IDverified Records"    : len(
				[verification for verification in verifications if verification.idverified is True]),
			"Active Servers"        : len([server for server in servers if server.active == 1])
		}

		embed = discord.Embed(title="Database Info",
		                      description="Reminder: This data is only allowed to be shared with relevant parties.")
		for title, value in data.items() :
			embed.add_field(name=title, value=value, inline=False)
		await send_response(interaction, StringStorage.NO_SHARE_REMINDER, embed=embed, ephemeral=True)

	@app_commands.command()
	@app_commands.checks.has_permissions(manage_messages=True)
	async def get(self, interaction: discord.Interaction, user: discord.User) :
		"""[manage_messages] Gets the date of birth of the specified user."""
		if await self.whitelist(interaction) :
			logging.info(f"{interaction.user.name} tried to look up {user.name} but wasn't whitelisted")
			return
		await send_response(interaction, f"⌛ Looking up {user.mention}", ephemeral=True)
		logging.info(f"{interaction.user.name} to looked up {user.name}")
		userdata: Users = UserTransactions().get_user(user.id)
		user_status = VerificationTransactions().get_id_info(user.id)
		if not userdata :
			await interaction.followup.send(f"No entry available for {user.mention}")
			return
		if not permissions.check_dev(interaction.user.id) and (
				user not in interaction.guild.members or userdata.server != interaction.guild.name) :
			await interaction.followup.send(
				"The user is not in the server and the date of birth was not added in this server.")
			return
		data = {
			"user"            : userdata.uid,
			"date of birth"   : Encryption().decrypt(userdata.date_of_birth) if userdata.date_of_birth else None,
			"Reason"          : user_status.reason if user_status else None,
			"idcheck"         : user_status.idcheck if user_status else None,
			"idverified"      : user_status.idverified if user_status else None,
			"verifieddob"     : user_status.verifieddob if user_status else None,
			"last updated in" : userdata.server,
			"deleted_at"      : userdata.deleted_at if userdata.deleted_at else None
		}

		embed = discord.Embed(title="USER INFO",
		                      description="Reminder: This data is only allowed to be shared with relevant parties.")
		for title, value in data.items() :
			embed.add_field(name=title, value=value, inline=False)
		await send_response(interaction, StringStorage.NO_SHARE_REMINDER, embed=embed, ephemeral=True)

	@app_commands.command()
	@app_commands.checks.has_permissions(manage_messages=True)
	async def create(self, interaction: discord.Interaction, user: discord.User, dob: str) :
		"""[manage_messages] Add the date of birth of the specified user to the database"""
		await send_response(interaction, f"⌛ adding {user.mention} to the database", ephemeral=True)
		if await self.whitelist(interaction) :
			return send_response(interaction, f"Server not whitelisted", ephemeral=True)

		dob = await AgeCalculations.validatedob(dob, interaction)
		if dob is False :
			return send_response(interaction, "Invalid date of birth format. Please use mm/dd/yyyy.")
		UserTransactions().add_user_full(str(user.id), dob, interaction.guild.name)
		await send_response(interaction, f"{user.name}({user.id}) added to the database with dob: {dob}")
		await LobbyProcess.age_log(user.id, dob, interaction)

	@app_commands.command()
	@app_commands.checks.has_permissions(manage_messages=True)
	async def update(self, interaction: discord.Interaction, user: discord.User, dob: str) :
		"""[manage_messages] updates the date of birth of a specified user."""
		await send_response(interaction, f"⌛ updating {user.mention}'s entry", ephemeral=True)

		if UserTransactions().get_user(user.id) is None :
			return await send_response(interaction, "User not found.")
		if await self.whitelist(interaction) :
			return
		dob = await AgeCalculations.validatedob(dob, interaction)
		if dob is False :
			return
		UserTransactions().update_user_dob(user.id, dob, interaction.guild.name)
		await send_response(interaction, f"Updated ({user.name}){user.id}'s dob to {dob}")
		await LobbyProcess.age_log(user.id, dob, interaction, "updated")

	@app_commands.command()
	@app_commands.checks.has_permissions(administrator=True)
	async def delete(self, interaction: discord.Interaction, user: discord.User, reason: str) :
		"""[administrator] Deletes the date of birth of a specified user. Only use this to correct mistakes."""

		await send_response(interaction, f"⌛ deleting {user.mention} from the database", ephemeral=True)
		if await self.whitelist(interaction) :
			return
		if UserTransactions().soft_delete(user.id, interaction.guild.name) is False :
			await interaction.followup.send(f"Can't find entry: ({user.name}){user.id}")
			return
		await send_response(interaction, f"Deleted entry: ({user.name}){user.id} with reason: {reason}")
		await LobbyProcess.age_log(user.id, "", interaction, "deleted", False, reason=reason)


async def setup(bot) :
	"""Adds the cog to the bot."""
	await bot.add_cog(Database(bot))
