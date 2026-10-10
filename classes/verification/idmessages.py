"""The member's ID image while it waits for review, and the staff message that reviews it.

The image only ever lives in AgeVerifier's DM to the member (see docs/privacypolicy.md). That DM carries the
withdraw button (views.buttons.idwithdrawbutton), whose custom_id points at the staff review message, so both a
withdrawal and the 7 day expiry can close the review without storing the staff message anywhere else.
"""
import logging
import re
from datetime import timedelta

import discord
from discord.ext import commands

from databases.transactions.VerificationTransactions import VerificationTransactions
from resources.data.config_variables import ID_MESSAGE_RETENTION_DAYS

# custom_id of the withdraw button: the channel and message id of the staff review message.
WITHDRAW_ID_TEMPLATE = r"id_withdraw:(?P<channel_id>\d+):(?P<message_id>\d+)"


def withdraw_custom_id(channel_id: int, message_id: int) -> str :
	return f"id_withdraw:{channel_id}:{message_id}"


def staff_review_reference(dm_message: discord.Message) -> tuple[int, int] | None :
	"""The (channel id, message id) of the staff review message, read from the DM's withdraw button.
	None for DMs sent before the button existed, or when attaching it failed."""
	for row in dm_message.components :
		for component in getattr(row, "children", [row]) :
			match = re.fullmatch(WITHDRAW_ID_TEMPLATE, getattr(component, "custom_id", None) or "")
			if match :
				return int(match["channel_id"]), int(match["message_id"])
	return None


async def close_staff_review(bot: commands.Bot, channel_id: int, message_id: int, notice: str) -> None :
	"""Replaces the staff review message's text and removes its buttons, so staff can't act on an ID that is gone.
	The embed stays, so the record of who submitted remains in the channel."""
	try :
		channel = bot.get_channel(channel_id) or await bot.fetch_channel(channel_id)
		message = await channel.fetch_message(message_id)
		await message.edit(content=notice, view=None)
	except discord.HTTPException as e :
		# Staff deleted the message or the bot lost access; there is nothing left to act on either way.
		logging.info(f"Could not close the ID review message {message_id} in {channel_id}: {e}")


async def expire_id_messages(bot: commands.Bot) -> int :
	"""
	Deletes ID images that have waited for review longer than ID_MESSAGE_RETENTION_DAYS, and closes their
	staff review messages. The record is only cleared once the image is gone: a Discord error leaves it for
	the next run, while a member or message that no longer exists only has the record left to clear.
	Returns the number of records cleared.
	"""
	transactions = VerificationTransactions()
	cleared = 0
	for record in transactions.get_expired_idmessages(timedelta(days=ID_MESSAGE_RETENTION_DAYS)) :
		try :
			user = bot.get_user(record.uid) or await bot.fetch_user(record.uid)
			dm_channel = user.dm_channel or await user.create_dm()
			dm_message = await dm_channel.fetch_message(record.idmessage)
			reference = staff_review_reference(dm_message)
			await dm_message.delete()
		except discord.NotFound :
			reference = None
		except discord.HTTPException as e :
			logging.warning(f"Could not delete the expired ID message for {record.uid}, retrying next run: {e}")
			continue

		transactions.remove_idmessage(record.uid)
		cleared += 1
		if reference is not None :
			await close_staff_review(bot, *reference,
			                         f"<@{record.uid}>'s ID submission was not reviewed within {ID_MESSAGE_RETENTION_DAYS} days, "
			                         f"so the ID has been deleted. Ask them to submit it again if they still need to verify.")
	logging.info(f"Deleted {cleared} expired ID messages.")
	return cleared
