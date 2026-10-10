import logging

import discord
from discord_py_utilities.messages import send_response

from classes.verification.idmessages import WITHDRAW_ID_TEMPLATE, close_staff_review, withdraw_custom_id
from databases.transactions.VerificationTransactions import VerificationTransactions


class IdWithdrawButton(discord.ui.DynamicItem[discord.ui.Button], template=WITHDRAW_ID_TEMPLATE) :
	"""
	Sits on the DM that holds the member's ID. Pressing it withdraws their consent: the ID is deleted and the
	staff review message is closed. It does not clear an ID check staff put on the member, so withdrawing
	can't be used to get out of one.
	"""

	def __init__(self, channel_id: int, message_id: int) :
		super().__init__(discord.ui.Button(label="Withdraw consent and delete my ID", style=discord.ButtonStyle.red,
		                                   custom_id=withdraw_custom_id(channel_id, message_id)))
		self.channel_id = channel_id
		self.message_id = message_id

	@classmethod
	async def from_custom_id(cls, interaction: discord.Interaction, item: discord.ui.Button, match) :
		return cls(int(match["channel_id"]), int(match["message_id"]))

	async def callback(self, interaction: discord.Interaction) :
		# Deferred first: the message this button is on is about to be deleted.
		await interaction.response.defer(ephemeral=True)
		try :
			await interaction.message.delete()
		except discord.NotFound :
			pass
		except discord.HTTPException as e :
			logging.error(f"Could not delete the ID message for {interaction.user.id} on withdrawal: {e}", exc_info=True)
			return await send_response(interaction, "We couldn't delete your ID just now, please try again in a moment.",
			                           ephemeral=True)

		# Only the current submission's record points at this message; an older one was already cleared on resubmit.
		idcheck = VerificationTransactions().get_id_info(interaction.user.id)
		if idcheck and idcheck.idmessage == interaction.message.id :
			VerificationTransactions().remove_idmessage(interaction.user.id)
		logging.info(f"[ID Withdraw] {interaction.user.id} withdrew consent and deleted their ID.")

		await close_staff_review(interaction.client, self.channel_id, self.message_id,
		                         f"{interaction.user.mention} withdrew their consent, and their ID has been deleted. "
		                         f"Ask them to verify again if they still need to.")
		await send_response(interaction,
		                    "Your ID has been deleted and the review has been cancelled; staff can no longer view it. "
		                    "If you still need to verify, you can start again from the server.",
		                    ephemeral=True)


async def attach_withdraw_button(dm_message: discord.Message, staff_message: discord.Message) :
	"""Adds the withdraw button to the member's ID DM, once the staff review message exists to point it at."""
	view = discord.ui.View(timeout=None)
	view.add_item(IdWithdrawButton(staff_message.channel.id, staff_message.id))
	try :
		await dm_message.edit(view=view)
	except discord.HTTPException as e :
		# The ID is still deleted after review or 7 days; only the early withdrawal is unavailable.
		logging.warning(f"Could not add the withdraw button to the ID message {dm_message.id}: {e}")
