"""Shared helpers for surfacing pending GDPR removals.

A removal request only soft-deletes the user: the record is hidden for a grace period and
purged afterwards. Everything that needs to tell a user or a staff member about that pending
state reads it from here, so the wording and the date stay consistent across the bot.

This lives in its own module rather than in classes/helpers.py because helpers.py imports
VerifyButton at module level, and the verification buttons are exactly what needs these
helpers - importing them from there would be circular.
"""
import logging
from datetime import datetime

import discord

from databases.transactions.UserTransactions import UserTransactions
from views.buttons.confirm import Confirm


def format_removal_date(when: datetime) -> str :
	"""Renders a removal date as an absolute timestamp plus a relative one."""
	return f"{discord.utils.format_dt(when, style='F')} ({discord.utils.format_dt(when, style='R')})"


def pending_removal_date(user_id: int) -> str | None :
	"""Formatted removal date for a user with a pending removal, or None if there isn't one."""
	when = UserTransactions().get_pending_removal(user_id)
	if when is None :
		return None
	return format_removal_date(when)


async def confirm_removal_cancellation(interaction: discord.Interaction) -> tuple[bool, discord.Interaction] :
	"""Asks a user with a pending removal whether verifying should cancel it.

	Storing a date of birth again clears deleted_at, which silently undoes the user's own
	erasure request, so we make them say yes to that first.

	Returns (proceed, interaction). The returned interaction is the one the rest of the flow
	must respond on: confirming consumes the original, and send_response's already-responded
	fallback would post the follow-up publicly in the lobby instead of ephemerally.
	"""
	removal_date = pending_removal_date(interaction.user.id)
	if removal_date is None :
		return True, interaction

	view = Confirm()
	confirmed = await view.send_confirm(
		interaction,
		f"{interaction.user.mention} You have asked for your data to be removed. It is scheduled to be "
		f"permanently deleted on or shortly after {removal_date}.\n\n"
		f"Verifying here stores your date of birth again, which **cancels that removal**. "
		f"Do you want to continue?",
		cancelled_message="Cancelled. Your data removal is still scheduled and nothing new was stored.",
		save_interaction=True,
	)

	if not confirmed :
		logging.info(f"[GDPR] {interaction.user.id} declined to cancel their pending removal.")
		return False, interaction

	# save_interaction leaves the button interaction unresponded for us, but it also means the
	# prompt is never tidied up (an ephemeral message can't be deleted), so clear it here using
	# the original interaction, which still owns that response.
	try :
		await interaction.edit_original_response(content="Confirmed", view=None)
	except discord.HTTPException :
		pass

	logging.info(f"[GDPR] {interaction.user.id} chose to cancel their pending removal by verifying.")
	return True, view.interaction or interaction
