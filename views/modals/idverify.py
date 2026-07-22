import logging

import discord
from discord_py_utilities.messages import send_response

from classes.AgeCalculations import AgeCalculations
from databases.transactions.ConfigData import ConfigData
from views.buttons.IDConfirm import IDConfirm


class IdVerifyModal(discord.ui.Modal) :
	# Our modal classes MUST subclass `discord.ui.Modal`,
	# but the title can be whatever you want.

	def __init__(self, user: discord.Member, message: discord.Message, reverify: bool = False) -> None :
		self.user: discord.Member = user
		self.message = message
		self.reverify = reverify
		super().__init__()

	title = "Verify your age"
	custom_id = "IDVerifyModal"

	dateofbirth = discord.ui.TextInput(
		label='Date of Birth (mm/dd/yyyy)',
		placeholder='mm/dd/yyyy',
		max_length=10
	)

	# Requires age checks, and then needs to send a message to the lobby channel; also make the lobby channel a config item.
	# Add in all the checks before it even gets to the lobby; age matches dob, dob already exists but diff?

	async def on_submit(self, interaction: discord.Interaction) :
		# validates inputs with regex
		if AgeCalculations.validate_dob(self.dateofbirth.value) is None :
			return await send_response(interaction, f"Please fill in the date of birth as with the format: mm/dd/yyyy.")

		idcheckchannel = ConfigData().get_key_int_or_zero(interaction.guild.id, "verification_failure_log")
		return await send_response(interaction,
		                           f"Please confirm the Date of Birth matches the user's ID you viewed via DMs and that you personally reviewed the ID. Submitting a DOB without viewing the ID or maliciously adding a false date of births may result in blacklisting. If `{self.dateofbirth.value}` is correct for {self.user.mention}, please click `Confirm & Proceed`.",
		                           view=IDConfirm(self.dateofbirth.value, self.user, self.message, reverify=self.reverify),
		                           ephemeral=True)

	async def on_error(self, interaction: discord.Interaction, error: Exception) -> None :
		logging.error(f"Error in {type(self).__name__}: {error}", exc_info=True)
		await send_response(interaction, 'Oops! Something went wrong.\n'
		                                        f'{error}')
