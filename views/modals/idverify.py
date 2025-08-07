import discord
from discord_py_utilities.messages import send_response

from classes.AgeCalculations import AgeCalculations
from classes.idverify import verify
from classes.support.queue import Queue


class IdVerifyModal(discord.ui.Modal) :
	# Our modal classes MUST subclass `discord.ui.Modal`,
	# but the title can be whatever you want.

	def __init__(self, user, message: discord.Message) :
		self.user = user
		self.message = message
		super().__init__()

	title = "Verify your age"
	custom_id = "NsfwVerify"

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
		await verify(self.user, interaction, self.dateofbirth.value, True)
		Queue().add(self.message.delete())
		await send_response(interaction, "User's ID verification entry has been updated.")

	async def on_error(self, interaction: discord.Interaction, error: Exception) -> None :
		print(error)
		await send_response(interaction, 'Oops! Something went wrong.\n'
		                                        f'{error}')
		raise error
