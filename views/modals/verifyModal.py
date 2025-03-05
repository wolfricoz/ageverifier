import logging

import discord

import databases.current
from classes.AgeCalculations import AgeCalculations
from classes.databaseController import ConfigData, UserTransactions
from classes.encryption import Encryption
from classes.idcheck import IdCheck
from classes.lobbyprocess import LobbyProcess
from classes.support.discord_tools import send_message, send_response
from classes.whitelist import check_whitelist
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
			required=True

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
		userdata: databases.current.Users = UserTransactions.get_user(interaction.user.id)
		mod_lobby = ConfigData().get_key_int(interaction.guild.id, "lobbymod")
		id_log = ConfigData().get_key_int(interaction.guild.id, "idlog")
		mod_channel = interaction.guild.get_channel(mod_lobby)
		id_channel = interaction.guild.get_channel(id_log)
		age = int(self.age.value)
		# validates inputs with regex
		if mod_channel is None or id_channel is None :
			await send_response(interaction, f"An error occurred: Lobby channel or ID channel not found.", ephemeral=False)

		dob = await AgeCalculations.infocheck(interaction, self.age.value, f"{self.month}/{self.day}/{self.year}", mod_channel)
		if dob is None :
			return
		# Checks if user is underaged
		agechecked, years = AgeCalculations.agechecker(age, dob)
		if age < 18 or years < 18 :
			return await IdCheck.send_check(interaction, mod_channel, "underage", age, dob, id_check=True,
			                                verify_button=False)
		logging.debug(f"userid: {interaction.user.id} age: {age} dob: {Encryption().encrypt(dob)}")
		# Checks if the age matches the date of birth, if only off by one year the can resubmit; otherwise they are flagged
		if agechecked == 1 or agechecked == -1 :
			return await IdCheck.send_check(interaction, mod_channel, "mismatch", age, dob, years=years, verify_button=False)
		if agechecked > 1 or agechecked < -1 :
			return await IdCheck.send_check(interaction, id_channel, "nomatch", age, dob, years=years, id_check=True)
		# Checks if user has a date of birth in the database, and if the date of births match.
		if AgeCalculations.check_date_of_birth(userdata, dob) is False :
			return await IdCheck.send_check(interaction, id_channel, "dobmismatch", age, dob,
			                                date_of_birth=Encryption().decrypt(userdata.date_of_birth), id_check=True)
		# Check if user needs to ID or has previously ID'd
		if idcheckinfo := await AgeCalculations.id_check_or_id_verified(interaction.user, interaction.guild, mod_channel) :
			return await IdCheck.send_check(interaction, id_channel, "idcheck", age, dob, id_check_reason=idcheckinfo.reason)
		# Sends the buttons and information to lobby channel
		if ConfigData().get_key(interaction.guild.id, "automatic") == "enabled".upper() :
			await LobbyProcess.approve_user(interaction.guild, interaction.user, dob, age, "Automatic")
			await send_response(interaction,
			                    f'Thank you for submitting your age and dob! You will be let through immediately!',
			                    ephemeral=True)
			return
		await AgeCalculations.check_history(interaction.guild.id, interaction.user, mod_channel)

		if check_whitelist(interaction.guild.id) :
			await send_message(mod_channel,
			                   f"\n{interaction.user.mention} has given {age} {dob}. You can let them through with the buttons below."
			                   f"\n-# [LOBBY DEBUG] To manually process: `?approve {interaction.user.mention} {age} {dob}`",
			                   view=ApprovalButtons(age=age, dob=dob, user=interaction.user))
			await send_response(interaction, f'Thank you for submitting your age and dob! You will be let through soon!',
			                    ephemeral=True)
			return
		await send_message(mod_channel,
		                   f"\n{interaction.user.mention} has given {age} and dob matches. You can let them through with the buttons below."
		                   f"\n-# [LOBBY DEBUG] Server not whitelisted: Personal Information (PI) hidden",
		                   view=ApprovalButtons(age=age, dob=dob, user=interaction.user))
		await send_response(interaction, f'Thank you for submitting your age and dob! You will be let through soon!',
		                    ephemeral=True)

	async def on_error(self, interaction: discord.Interaction, error: Exception) -> None :
		print(error)
		await send_response(interaction, f"An error occurred: {error}", ephemeral=True)
		raise error
