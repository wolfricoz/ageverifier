import logging

import discord
from discord_py_utilities.messages import send_response

from classes.AgeCalculations import AgeCalculations
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
		dob = self.normalise_dob(self.dateofbirth.value)
		if dob is None :
			return await send_response(interaction, "Please enter the date of birth as mm/dd/yyyy (dd/mm/yyyy also works when the day is 13 or higher).")

		# Staff confirm (and we store) the normalised mm/dd/yyyy date, never the raw input such as '12262008' (AGEVERIFIER-D7).
		return await send_response(interaction,
		                           f"Please confirm the Date of Birth matches the user's ID you viewed via DMs and that you personally reviewed the ID. Submitting a DOB without viewing the ID or maliciously adding a false date of births may result in blacklisting. If `{dob}` is correct for {self.user.mention}, please click `Confirm & Proceed`.",
		                           view=IDConfirm(dob, self.user, self.message, reverify=self.reverify),
		                           ephemeral=True)

	@staticmethod
	def normalise_dob(value: str) -> str | None :
		"""Returns the date of birth as mm/dd/yyyy, or None when it can't be read."""
		value = value.strip()
		if AgeCalculations.validate_dob(value) is None :
			return None
		try :
			return AgeCalculations.dob_regex(AgeCalculations.add_slashes_to_dob(value))
		except ValueError :
			return None

	async def on_error(self, interaction: discord.Interaction, error: Exception) -> None :
		logging.error(f"Error in {type(self).__name__}: {error}", exc_info=True)
		await send_response(interaction, 'Oops! Something went wrong.\n'
		                                        f'{error}')
