import logging

import discord
from discord_py_utilities.messages import send_message, send_response

import databases.current
from classes.AgeCalculations import AgeCalculations
from classes.encryption import Encryption
from classes.idcheck import IdCheck
from classes.lobbyprocess import LobbyProcess
from classes.lobbytimers import LobbyTimers
from classes.whitelist import check_whitelist
from databases.controllers.AgeRoleTransactions import AgeRoleTransactions
from databases.controllers.ButtonTransactions import LobbyDataTransactions
from databases.controllers.ConfigData import ConfigData
from databases.controllers.HistoryTransactions import JoinHistoryTransactions
from databases.controllers.UserTransactions import UserTransactions
from databases.enums.joinhistorystatus import JoinHistoryStatus
from views.buttons.approvalbuttons import ApprovalButtons


class VerifyModal(discord.ui.Modal) :
	# Our modal classes MUST subclass `discord.ui.Modal`,
	# but the title can be whatever you want.
	title = "Verify your age"
	custom_id = "verify"

	# This will be a short input, where the user can enter their name
	# It will also have a placeholder, as denoted by the `placeholder` kwarg.
	# By default, it is required and is a short-style input which is exactly
	# what we want.

	def __init__(self, month=2, day=3, year=4) :
		super().__init__()
		self.age = discord.ui.TextInput(
			label='Current Age (Do not round up or down)',
			placeholder='99',
			max_length=3,
			style=discord.TextStyle.short,
			required=True,
			row=0

		)
		self.month = discord.ui.TextInput(
			label='month',
			placeholder='mm',
			max_length=2,
			style=discord.TextStyle.short,
			row=month,
			required=True

		)

		self.day = discord.ui.TextInput(
			label='day',
			placeholder='dd',
			max_length=2,
			style=discord.TextStyle.short,
			row=day,
			required=True

		)

		self.year = discord.ui.TextInput(
			label='year',
			placeholder='yyyy',
			max_length=4,
			style=discord.TextStyle.short,
			row=year,
			required=True
		)
		self.add_item(self.age)
		self.add_item(self.day)
		self.add_item(self.month)
		self.add_item(self.year)

	async def on_submit(self, interaction: discord.Interaction) :
		userdata: databases.current.Users = UserTransactions().get_user(interaction.user.id)
		mod_lobby = ConfigData().get_key_int_or_zero(interaction.guild.id, "lobbymod")
		id_log = ConfigData().get_key_int_or_zero(interaction.guild.id, "idlog")
		mod_channel = interaction.guild.get_channel(mod_lobby)
		id_channel = interaction.guild.get_channel(id_log)
		if mod_channel is None or id_channel is None:
			await send_response(interaction, f"Lobbymod or id_channel not set, inform the server staff to setup the server.",
			                    ephemeral=True)

			return
		age = int(self.age.value)
		# validates inputs with regex
		if mod_channel is None or id_channel is None :
			await send_response(interaction, f"An error occurred: Lobby channel or ID channel not found.", ephemeral=False)

		dob = await AgeCalculations.infocheck(interaction, self.age.value, f"{self.month}/{self.day}/{self.year}",
		                                      mod_channel)
		if dob is None :
			return None
		# Checks if user is underaged
		agechecked, years = AgeCalculations.agechecker(age, dob)
		minimum_age = AgeRoleTransactions().get_minimum_age(interaction.guild.id)
		if age < 18 or years < 18 :
			JoinHistoryTransactions().update(interaction.user.id, interaction.guild.id, JoinHistoryStatus.IDCHECK)
			await IdCheck.send_check(interaction, mod_channel, "underage", age, dob, id_check=True,
			                         verify_button=False, server=interaction.guild.name)
			await self.autokick(interaction, mod_channel, age, minimum_age)
			return None
		if minimum_age and age < minimum_age :
			await send_response(interaction,
			                    f'Thank you for submitting your date of birth, unfortunately you are too young for this server; you must be {minimum_age} years old.',
			                    ephemeral=True)
			await self.autokick(interaction, mod_channel, age, minimum_age)
			return None

		logging.debug(f"userid: {interaction.user.id} age: {age} dob: {Encryption().encrypt(dob)}")
		# Checks if the age matches the date of birth, if only off by one year the can resubmit; otherwise they are flagged
		if agechecked == 1 or agechecked == -1 :
			return await IdCheck.send_check(interaction, mod_channel, "mismatch", age, dob, years=years, verify_button=False)

		if agechecked > 1 or agechecked < -1 :
			JoinHistoryTransactions().update(interaction.user.id, interaction.guild.id, JoinHistoryStatus.IDCHECK)
			return await IdCheck.send_check(interaction, id_channel, "nomatch", age, dob, years=years, id_check=True,
			                                server=interaction.guild.name)
		# Checks if user has a date of birth in the database, and if the date of births match.
		if AgeCalculations.check_date_of_birth(userdata, dob) is False :
			JoinHistoryTransactions().update(interaction.user.id, interaction.guild.id, JoinHistoryStatus.IDCHECK)
			return await IdCheck.send_check(interaction, id_channel, "dobmismatch", age, dob,
			                                date_of_birth=Encryption().decrypt(userdata.date_of_birth), id_check=True,
			                                server=userdata.server)
		# Check if user needs to ID or has previously ID'd
		if idcheckinfo := await AgeCalculations.id_check_or_id_verified(interaction.user, interaction.guild, mod_channel) :
			JoinHistoryTransactions().update(interaction.user.id, interaction.guild.id, JoinHistoryStatus.IDCHECK)
			return await IdCheck.send_check(interaction, id_channel, "idcheck", age, dob, id_check_reason=idcheckinfo.reason,
			                                server=idcheckinfo.server)
		# Sends the buttons and information to lobby channel

		automatic_status = ConfigData().get_key_or_none(interaction.guild.id, "automatic")
		if automatic_status and automatic_status == "enabled".upper() :
			await LobbyProcess.approve_user(interaction.guild, interaction.user, dob, age, "Automatic")
			await send_response(interaction,
			                    f'Thank you for submitting your age and dob! You will be let through immediately!',
			                    ephemeral=True)
			return None
		await AgeCalculations.check_history(interaction.guild.id, interaction.user, mod_channel)
		LobbyTimers().add_cooldown(interaction.guild.id, interaction.user.id,
		                           ConfigData().get_key_int_or_zero(interaction.guild.id, 'COOLDOWN'))
		approval_buttons = ApprovalButtons(age=age, dob=dob, user=interaction.user)
		await send_response(interaction, f'Thank you for submitting your age and dob! You will be let through soon!',
		                    ephemeral=True)
		await approval_buttons.send_message(interaction, mod_channel)


		return None

	async def on_error(self, interaction: discord.Interaction, error: Exception) -> None :
		print(error)
		await send_response(interaction, f"An error occurred: {error}", ephemeral=True)
		raise error

	async def autokick(self, interaction, mod_channel, age, minimum_age) :
		if ConfigData().get_key(interaction.guild.id, "AUTOKICK") == "ENABLED" :
			await send_message(interaction.user,
			                   f"Thank you for submitting your date of birth, unfortunately you are too young for this server; you must be {minimum_age} years old.")
			await send_message(mod_channel,
			                   f"\n{interaction.user.mention} has given {age} which is below the minimum age of the age roles and has been denied entry. The user has been kicked because autokick is turned on.")
			await interaction.user.kick(reason="user under minimum age")
			return
		await send_message(mod_channel,
		                   f"\n{interaction.user.mention} has given {age} which is below the minimum age of the age roles and has been denied entry.")
