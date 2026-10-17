"""The message a member gets when staff deny their verification with a preset reason (STR-84)."""
import logging

import discord

# Discord rejects a message longer than this.
DM_LIMIT = 2000


def fill_placeholders(message: str, user: discord.abc.User, guild: discord.Guild) -> str :
	"""
	Replaces {user} and {server} in a preset message. Plain replacement rather than str.format, so
	any other braces staff type are left alone instead of raising or reaching into objects.
	"""
	return message.replace("{user}", user.mention).replace("{server}", guild.name)


def denial_message(label: str, message: str, user: discord.abc.User, guild: discord.Guild) -> str :
	"""The DM sent to the member: what went wrong (the label), then the preset's explanation and next steps."""
	header = (f"**Your age verification in {guild.name} was not approved**\n"
	          f"**Reason:** {label}\n\n")
	footer = (f"\n\n-# Sent on behalf of the staff of {guild.name}. Replies to this message are not read; "
	          f"please contact the server's staff if you have questions.")
	body = fill_placeholders(message, user, guild)
	# Presets fit as typed, but every {server} can add up to 100 characters.
	room = DM_LIMIT - len(header) - len(footer)
	if len(body) > room :
		body = body[:room - 1] + "…"
	return header + body + footer


async def send_denial(user: discord.abc.User, guild: discord.Guild, label: str, message: str) -> bool :
	"""
	DMs the denial to the member. A member with closed DMs, or who can no longer be reached, is
	skipped without an error.

	:return: whether the DM was delivered.
	"""
	try :
		await user.send(denial_message(label, message, user, guild))
		return True
	except (discord.Forbidden, discord.HTTPException) as e :
		logging.info(f"Unable to send the denial message to {user.id} in {guild.id}: {e}")
		return False
