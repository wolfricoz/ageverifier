"""Adds or edits one of a server's denial reason presets (/config denial_reasons)."""
import logging

import discord
from discord_py_utilities.messages import send_response

from classes.config.utils import ConfigUtils
from classes.support.queue import Queue
from databases.current import DenialReasons
from databases.transactions.DenialReasonTransactions import DenialReasonTransactions
from resources.data.config_variables import MAX_DENIAL_LABEL_LENGTH, MAX_DENIAL_MESSAGE_LENGTH, MAX_DENIAL_REASONS


class DenialReasonModal(discord.ui.Modal, title="Denial reason") :
	reason = discord.ui.TextInput(label="Reason (shown to staff and the member)", style=discord.TextStyle.short,
	                              placeholder="Age and date of birth don't match", max_length=MAX_DENIAL_LABEL_LENGTH)
	details = discord.ui.TextInput(label="Message to the member",
	                               style=discord.TextStyle.long,
	                               placeholder="What went wrong, and what should they do next? {user} and {server} are filled in.",
	                               max_length=MAX_DENIAL_MESSAGE_LENGTH)

	def __init__(self, existing: DenialReasons = None) :
		super().__init__(timeout=None)
		self.existing = existing
		if existing is not None :
			self.reason.default = existing.label
			self.details.default = existing.message

	async def on_submit(self, interaction: discord.Interaction) :
		label = self.reason.value.strip()
		message = self.details.value.strip()
		if not label or not message :
			await send_response(interaction, "The reason and the message can't be empty.", ephemeral=True)
			return
		transactions = DenialReasonTransactions()
		exclude = self.existing.id if self.existing is not None else None
		if transactions.label_taken(interaction.guild.id, label, exclude_id=exclude) :
			await send_response(interaction, f"There already is a denial reason called **{label}**.", ephemeral=True)
			return

		if self.existing is None :
			# Checked again here: presets can be added from another modal while this one was open.
			if transactions.count(interaction.guild.id) >= MAX_DENIAL_REASONS :
				await send_response(interaction, f"A server can have up to {MAX_DENIAL_REASONS} denial reasons, remove one first.",
				                    ephemeral=True)
				return
			transactions.add(interaction.guild.id, label, message)
			change, reply = "denial reason added", f"Denial reason **{label}** added."
		else :
			if not transactions.update(interaction.guild.id, self.existing.id, label, message) :
				await send_response(interaction, "That denial reason no longer exists.", ephemeral=True)
				return
			change, reply = "denial reason edited", f"Denial reason **{label}** saved."
		Queue().add(ConfigUtils.log_change(interaction.guild, {change : label}, user_name=interaction.user.mention))
		await send_response(interaction, reply, ephemeral=True)

	async def on_error(self, interaction: discord.Interaction, error: Exception) -> None :
		logging.error(f"Error in {type(self).__name__}: {error}", exc_info=True)
		await send_response(interaction, 'Oops! Something went wrong.', ephemeral=True)
