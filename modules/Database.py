"""this module handles the lobby."""
import datetime
import logging
from datetime import datetime, timedelta

import discord
from discord import app_commands
from discord.ext import commands
from discord_py_utilities.messages import send_response

import classes.permissions as permissions
from classes.AgeCalculations import AgeCalculations
from classes.encryption import Encryption
from classes.lobbyprocess import LobbyProcess
from classes.whitelist import whitelist
from databases.current import Users
from databases.transactions.ServerTransactions import ServerTransactions
from databases.transactions.UserTransactions import UserTransactions
from databases.transactions.VerificationTransactions import VerificationTransactions
from resources.data.responses import StringStorage


class Database(commands.GroupCog, name="database") :
	"""
	Commands for interacting with the user database.
	Most of these commands are restricted to whitelisted servers and require elevated permissions.
	"""
	def __init__(self, bot: commands.Bot) :
		self.bot = bot
		self.index = 0

	#     @app_commands.choices(operation=[Choice(name=x, value=x) for x in
	#                                      ["VERIFICATION_ADD_ROLE", 'update', 'delete', 'get']])


	@app_commands.command()
	@app_commands.checks.has_permissions(manage_messages=True)
	async def stats(self, interaction: discord.Interaction) :
		"""
        Displays various statistics from the bot's database.
        This provides a general overview of things like the number of user records, verifications, and active servers.
        This information is maintained for administrative purposes and transparency.

        **Permissions:**
        - You'll need the `Manage Messages` permission to use this command.
        """
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
		"""
        Looks up and displays the database entry for a specific user.
        This includes their stored date of birth and verification status. This command is restricted to whitelisted servers for privacy and security reasons.
        The information provided is sensitive and should be handled with care - Do not share it with non-whitelisted parties; they should use the verification system instead or contact support.

        **Permissions:**
        - You'll need the `Manage Messages` permission.
        - Your server must be whitelisted to use this feature.
        """
		if await whitelist(interaction) :
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
		"""
        Manually creates a new database entry for a user with their date of birth.
        This is useful for adding users who may have had issues with the automated system. The date of birth should be in `mm/dd/yyyy` format.
        This command is restricted to whitelisted servers.

        Non-whitelisted servers can use the buttons in the verification system to achieve the same result.

        **Permissions:**
        - You'll need the `Manage Messages` permission.
        - Your server must be whitelisted to use this feature.
        """
		await send_response(interaction, f"⌛ adding {user.mention} to the database", ephemeral=True)
		if await whitelist(interaction) :
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
		"""
        Updates the date of birth for a user who is already in the database.
        Use this to correct any errors in a user's stored information. The date of birth should be in `mm/dd/yyyy` format.
        This command is restricted to whitelisted servers.

        Non-whitelisted servers can open a ticket in the support server to have a developer update the user's information.


        **Permissions:**
        - You'll need the `Manage Messages` permission.
        - Your server must be whitelisted to use this feature.
        """
		await send_response(interaction, f"⌛ updating {user.mention}'s entry", ephemeral=True)

		if UserTransactions().get_user(user.id) is None :
			return await send_response(interaction, "User not found.")
		if await whitelist(interaction) :
			return
		dob = await AgeCalculations.validatedob(dob, interaction)
		if dob is False :
			return None
		UserTransactions().update_user_dob(user.id, dob, interaction.guild.name)
		await send_response(interaction, f"Updated ({user.name}){user.id}'s dob to {dob}")
		await LobbyProcess.age_log(user.id, dob, interaction, "updated")

	@app_commands.command()
	@app_commands.checks.has_permissions(administrator=True)
	async def delete(self, interaction: discord.Interaction, user: discord.User, reason: str) :
		"""
        Deletes a user's entry from the database.
        This should only be used to correct significant mistakes or for privacy requests. A reason for the deletion is required for logging purposes.
        This command is restricted to whitelisted servers.

        Non-whitelisted servers can open a ticket in the support server to have a developer delete the user's information.

        **Permissions:**
        - You'll need the `Administrator` permission.
        - Your server must be whitelisted to use this feature.
        """

		await send_response(interaction, f"⌛ deleting {user.mention} from the database", ephemeral=True)
		if await whitelist(interaction) :
			return
		if UserTransactions().soft_delete(user.id, interaction.guild.name) is False :
			await interaction.followup.send(f"Can't find entry: ({user.name}){user.id}")
			return
		await send_response(interaction, f"Deleted entry: ({user.name}){user.id} with reason: {reason}")
		await LobbyProcess.age_log(user.id, "", interaction, "deleted", False, reason=reason)


async def setup(bot) :
	"""Adds the cog to the bot."""
	await bot.add_cog(Database(bot))
