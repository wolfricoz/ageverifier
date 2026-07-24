import discord.ui

from discord_py_utilities.messages import send_response


class Confirm(discord.ui.View):

	"""This class is for the confirm buttons, which are used to confirm or cancel an action."""


	async def send_confirm(self, interaction: discord.Interaction, message: str = "Do you want to proceed?", cancelled_message = "Cancelled", save_interaction: bool = False):
		"""send the confirm message"""

		await send_response(interaction, message, view=self, ephemeral=True)
		self.cancel_message = cancelled_message
		self.save_interaction = save_interaction
		await self.wait()

		return self.value

	def __init__(self):
		super().__init__(timeout=1200)
		self.save_interaction = None
		self.cancel_message = None
		self.interaction = None
		self.value = None

	async def _finish(self, interaction: discord.Interaction, content: str):
		"""Replace the prompt with a result message and remove the buttons."""
		try:
			await interaction.response.edit_message(content=content, view=None)
		except discord.HTTPException:
			pass

	@discord.ui.button(label="Confirm", style=discord.ButtonStyle.green, custom_id="confirm")
	async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
		"""confirm the action"""
		self.value = True
		self.interaction = interaction
		if self.save_interaction:
			# Leave the interaction unresponded so the caller can open a modal on it.
			try:
				await interaction.message.delete()
			except discord.HTTPException:
				pass
		else:
			await self._finish(interaction, "Confirmed")
		self.stop()

	@discord.ui.button(label="Cancel", style=discord.ButtonStyle.red, custom_id="cancel")
	async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
		"""cancel the action"""
		self.value = False
		self.interaction = interaction
		await self._finish(interaction, self.cancel_message)
		self.stop()
