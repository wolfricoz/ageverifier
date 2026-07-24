import discord.ui

from discord_py_utilities.messages import send_response


class ReasonChoice(discord.ui.View):
	"""Prompt shown when the target user is already on the ID check list.

	Replaces an overloaded Confirm/Cancel with three clearly-labelled
	choices so staff know exactly what each button does:
	  - Update reason        -> enter a new reason, then send the request
	  - Keep existing reason -> send the request using the stored reason
	  - Cancel               -> abort, sending nothing
	"""

	UPDATE = "update"
	KEEP = "keep"
	CANCEL = "cancel"

	def __init__(self):
		super().__init__(timeout=1200)
		self.value = None
		self.interaction = None

	async def prompt(self, interaction: discord.Interaction, message: str):
		"""Show the buttons and wait for a choice.

		Returns UPDATE, KEEP or CANCEL, or None if the prompt times out.
		"""
		await send_response(interaction, message, view=self, ephemeral=True)
		await self.wait()
		return self.value

	@discord.ui.button(label="Update reason", style=discord.ButtonStyle.green, custom_id="reason_update")
	async def update(self, interaction: discord.Interaction, button: discord.ui.Button):
		"""Overwrite the stored reason.

		Leaves the interaction unresponded on purpose so the caller can open
		a modal on it (a modal must be sent as the interaction's response).
		The now-stale buttons are stripped by ``clear_buttons`` afterwards.
		"""
		self.value = self.UPDATE
		self.interaction = interaction
		self.stop()

	@discord.ui.button(label="Keep existing reason", style=discord.ButtonStyle.blurple, custom_id="reason_keep")
	async def keep(self, interaction: discord.Interaction, button: discord.ui.Button):
		"""Send the request using the reason already on file."""
		self.value = self.KEEP
		self.interaction = interaction
		await self._resolve(interaction, "Sending the request with the existing reason…")

	@discord.ui.button(label="Cancel", style=discord.ButtonStyle.grey, custom_id="reason_cancel")
	async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
		"""Abort — no ID request is sent."""
		self.value = self.CANCEL
		self.interaction = interaction
		await self._resolve(interaction, "Cancelled — no ID request was sent.")

	async def _resolve(self, interaction: discord.Interaction, content: str):
		"""Replace the prompt with a result message and remove the buttons."""
		try:
			await interaction.response.edit_message(content=content, view=None)
		except discord.HTTPException:
			pass
		self.stop()

	async def clear_buttons(self):
		"""Best-effort removal of the buttons after the update modal is shown.

		The update interaction is spent opening the modal, so the original
		prompt is edited through a followup instead. Any failure is harmless —
		the view is already stopped, so the stale buttons are inert.
		"""
		if self.interaction is None or self.interaction.message is None:
			return
		try:
			await self.interaction.followup.edit_message(self.interaction.message.id, view=None)
		except discord.HTTPException:
			pass
