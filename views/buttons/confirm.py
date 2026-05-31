import discord.ui

from discord_py_utilities.messages import send_response


class Confirm(discord.ui.View):

	"""This class is for the confirm buttons, which are used to confirm or cancel an action."""


	async def send_confirm(self, interaction: discord.Interaction, message: str = "Do you want to proceed?", cancelled_message = "Cancelled", save_interaction: bool = False):
		"""send the confirm message"""
		await send_response(interaction, message, view=self, ephemeral=True)
		await self.wait()
		self.cancel_message = cancelled_message
		self.save_interaction = save_interaction

		return self.value

	def __init__(self):
		super().__init__(timeout=None)
		self.save_interaction = None
		self.cancel_message = None
		self.interaction = None
		self.value = None

	@discord.ui.button(label="Confirm", style=discord.ButtonStyle.green, custom_id="confirm")
	async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
		"""confirm the action"""
		self.value = True
		try:
			await interaction.message.delete()
		except:
			pass
		self.interaction = interaction
		if not self.save_interaction:
			await send_response(interaction, "Confirmed", ephemeral=True)
		self.stop()

	@discord.ui.button(label="Cancel", style=discord.ButtonStyle.red, custom_id="cancel")
	async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
		"""cancel the action"""
		self.value = False
		self.interaction = interaction

		await send_response(interaction, self.cancel_message, ephemeral=True)
		self.stop()
		try:
			await interaction.message.delete()
		except:
			pass
