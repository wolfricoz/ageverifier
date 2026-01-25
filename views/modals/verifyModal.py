import logging

import discord
from discord_py_utilities.messages import send_message, send_response

from classes.encryption import Encryption
from classes.idcheck import IdCheck
from classes.verification.process import VerificationProcess
from databases.transactions.ConfigData import ConfigData


class VerifyModal(discord.ui.Modal) :
	# Our modal classes MUST subclass `discord.ui.Modal`,
	# but the title can be whatever you want.
	title = "Verify your age"
	custom_id = "verify"

	# This will be a short input, where the user can enter their name
	# It will also have a placeholder, as denoted by the `placeholder` kwarg.
	# By default, it is required and is a short-style input which is exactly
	# what we want.

	def __init__(self, month=2, day=3, year=4, reverify=False) :
		super().__init__()
		self.reverify = reverify
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
		# await interaction.response.defer(ephemeral=True)
		verification_process = VerificationProcess(
			interaction.client,
			interaction.user,
			interaction.guild,
			self.day.value,
			self.month.value,
			self.year.value,
			self.age.value,
			reverify=self.reverify
		)
		message = await verification_process.verify()
		if verification_process.error is not None :
			await send_response(interaction, f"Verification failed: {verification_process.error}", ephemeral=True)
			return
		if verification_process.discrepancy is not None :
			logging.info(f"discrepancy: {verification_process.discrepancy}")
			id_check = True

			if verification_process.discrepancy in ["age_too_high", "mismatch", "below_minimum_age"] :
				id_check = False
			return await IdCheck.send_check(interaction,
			                                verification_process.id_channel,
			                                verification_process.discrepancy,
			                                verification_process.age,
			                                verification_process.dob,
			                                date_of_birth=Encryption().decrypt(
				                                verification_process.user_record.date_of_birth)
			                                if verification_process.user_record is not None
			                                else None,
			                                years=verification_process.years if verification_process.years else None,
			                                id_check=id_check,
			                                id_check_reason=verification_process.id_check_info.reason if verification_process.id_check_info else verification_process.discrepancy,
			                                server=verification_process.id_check_info.server if verification_process.id_check_info else interaction.guild.name)

		return await send_response(interaction, message, ephemeral=True)

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
