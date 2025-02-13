"""this module handles the lobby."""
import datetime
import os

import discord
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands
from sqlalchemy import True_

import classes.permissions as permissions
from classes.AgeCalculations import AgeCalculations
from classes.databaseController import UserTransactions, ConfigData, VerificationTransactions
from classes.encryption import Encryption
from classes.helpers import has_onboarding, welcome_user, invite_info
from classes.idverify import verify
from classes.lobbyprocess import LobbyProcess
from classes.support.discord_tools import send_response, send_message
from classes.whitelist import check_whitelist
from databases.current import database, Users
from views.buttons.agebuttons import AgeButtons
from views.buttons.confirmButtons import confirmAction
from views.buttons.dobentrybutton import dobentry
from views.buttons.verifybutton import VerifyButton



class Database(commands.GroupCog) :
	def __init__(self, bot: commands.Bot) :
		self.bot = bot
		self.index = 0
		self.bot.add_view(VerifyButton())
		self.bot.add_view(AgeButtons())
		self.bot.add_view(dobentry())

	#     @app_commands.choices(operation=[Choice(name=x, value=x) for x in
	#                                      ['add', 'update', 'delete', 'get']])
	async def whitelist(self, interaction):
		if not check_whitelist(interaction.guild.id) and not permissions.check_dev(interaction.user.id) :
			await send_response(interaction, f"[NOT_WHITELISTED] This command is limited to whitelisted servers. Please join our [support server]({os.getenv('INVITE')}) and open a ticket to edit or send a message to `ricostryker`")
			return True
		return False

	@app_commands.command()
	@app_commands.checks.has_permissions(manage_messages=True)
	async def get(self, interaction: discord.Interaction, user: discord.User) :
		"""[manage_messages] Gets the date of birth of the specified user."""
		await send_response(interaction, f"⌛ Looking up {user.mention}", ephemeral=True)
		if await self.whitelist(interaction):
			return
		userdata: Users = UserTransactions.get_user(user.id)
		if not permissions.check_dev(interaction.user.id) and (
				user not in interaction.guild.members or userdata.server != interaction.guild.name) :
			await interaction.followup.send(
				"The user is not in the server and the date of birth was not added in this server.")
			return
		data = {
			"user"            : userdata.uid,
			"date of birth"   : Encryption().decrypt(userdata.date_of_birth),
			"last updated in" : userdata.server
		}

		embed = discord.Embed(title="USER INFO",
		                      description="Reminder: This data is only allowed to be shared with relevant parties.")
		for title, value in data.items() :
			embed.add_field(name=title, value=value, inline=False)
		await send_response(interaction,f"", embed=embed, ephemeral=True)

	@app_commands.command()
	@app_commands.checks.has_permissions(manage_messages=True)
	async def create(self, interaction: discord.Interaction, user: discord.User, dob: str) :
		"""[manage_messages] Add the date of birth of the specified user to the database"""
		await send_response(interaction, f"⌛ adding {user.mention} to the database", ephemeral=True)
		if await self.whitelist(interaction):
			return
		if await AgeCalculations.validatedob(dob, interaction) is False :
			return
		UserTransactions.add_user_full(str(user.id), dob, interaction.guild.name)
		await send_response(interaction, f"({user.name}){user.id} added to the database with dob: {dob}")
		await LobbyProcess.age_log(user.id, dob, interaction)


	@app_commands.command()
	@app_commands.checks.has_permissions(manage_messages=True)
	async def update(self, interaction: discord.Interaction, user: discord.User, dob: str) :
		"""[manage_messages] updates the date of birth of a specified user."""
		await send_response(interaction, f"⌛ updating {user.mention}'s entry", ephemeral=True)
		if await self.whitelist(interaction):
			return
		if await AgeCalculations.validatedob(dob, interaction) is False :
			return
		UserTransactions.update_user_dob(user.id, dob, interaction.guild.name)
		await send_response(interaction, f"Updated ({user.name}){user.id}'s dob to {dob}")
		await LobbyProcess.age_log(user.id, dob, interaction, "updated")


	@app_commands.command()
	@app_commands.checks.has_permissions(administrator=True)
	async def delete(self, interaction: discord.Interaction, user: discord.User, reason: str) :
		"""[administrator] Deletes the date of birth of a specified user. Only use this to correct mistakes."""

		await send_response(interaction, f"⌛ deleting {user.mention} from the database", ephemeral=True)
		if await self.whitelist(interaction):
			return
		if UserTransactions.user_delete(user.id, interaction.guild.name) is False :
			await interaction.followup.send(f"Can't find entry: ({user.name}){user.id}")
			return
		await send_response(interaction, f"Deleted entry: ({user.name}){user.id} with reason: {reason}")
		await LobbyProcess.age_log(user.id, "", interaction, "deleted", False)




async def setup(bot) :
	"""Adds the cog to the bot."""
	await bot.add_cog(Database(bot))
