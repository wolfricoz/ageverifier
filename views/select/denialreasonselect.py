"""The reason picker staff get after pressing Deny on an approval message (STR-84)."""
import logging
from typing import Awaitable, Callable

import discord
from discord_py_utilities.messages import send_response

from databases.current import DenialReasons
from resources.data.config_variables import MAX_DENIAL_LABEL_LENGTH, MAX_DENIAL_MESSAGE_LENGTH, MAX_DENIAL_REASONS

CUSTOM_VALUE = "custom"
# Select option descriptions are capped at 100 characters by Discord.
DESCRIPTION_LENGTH = 100

# Called with the interaction that picked the reason (not yet responded to), the label and the message.
OnPick = Callable[[discord.Interaction, str, str], Awaitable[None]]


def preview(message: str) -> str :
	flat = " ".join(message.split())
	return flat if len(flat) <= DESCRIPTION_LENGTH else flat[:DESCRIPTION_LENGTH - 1] + "…"


class DenialReasonView(discord.ui.View) :
	"""An ephemeral select of the guild's presets, plus a custom reason written on the spot."""

	def __init__(self, reasons: list[DenialReasons], on_pick: OnPick) :
		super().__init__(timeout=600)
		self.on_pick = on_pick
		self.done = False
		self.reasons = {str(reason.id) : reason for reason in reasons[:MAX_DENIAL_REASONS]}
		options = [discord.SelectOption(label=reason.label[:MAX_DENIAL_LABEL_LENGTH], value=key,
		                                description=preview(reason.message))
		           for key, reason in self.reasons.items()]
		options.append(discord.SelectOption(label="Custom reason", value=CUSTOM_VALUE, emoji="✏️",
		                                    description="Write a one-off message to the member"))
		self.select = discord.ui.Select(placeholder="Why is this verification denied?", options=options)
		self.select.callback = self.picked
		self.add_item(self.select)

	async def picked(self, interaction: discord.Interaction) :
		value = self.select.values[0]
		if value == CUSTOM_VALUE :
			await interaction.response.send_modal(CustomDenialModal(self.finish))
			return
		reason = self.reasons.get(value)
		if reason is None :
			await send_response(interaction, "That reason is no longer available, please pick another.", ephemeral=True)
			return
		await self.finish(interaction, reason.label, reason.message)

	async def finish(self, interaction: discord.Interaction, label: str, message: str) :
		# The custom modal leaves the select usable while it is open; only the first pick counts.
		if self.done :
			await send_response(interaction, "This verification has already been denied.", ephemeral=True)
			return
		self.done = True
		self.stop()
		await self.on_pick(interaction, label, message)


class CustomDenialModal(discord.ui.Modal, title="Deny with a custom reason") :
	reason = discord.ui.TextInput(label="Reason", style=discord.TextStyle.short, default="Other",
	                              max_length=MAX_DENIAL_LABEL_LENGTH)
	details = discord.ui.TextInput(label="Message to the member",
	                               style=discord.TextStyle.long,
	                               placeholder="What went wrong, and what should they do next? {user} and {server} are filled in.",
	                               max_length=MAX_DENIAL_MESSAGE_LENGTH)

	def __init__(self, on_submit: OnPick) :
		super().__init__(timeout=600)
		self.submit_callback = on_submit

	async def on_submit(self, interaction: discord.Interaction) :
		await self.submit_callback(interaction, self.reason.value.strip(), self.details.value.strip())

	async def on_error(self, interaction: discord.Interaction, error: Exception) -> None :
		logging.error(f"Error in {type(self).__name__}: {error}", exc_info=True)
		await send_response(interaction, "Oops! Something went wrong.", ephemeral=True)
