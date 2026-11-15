"""Checks that a server has the channels verification needs, and tells staff when it does not.

Verification posts approvals to the approval channel and ID checks to the failed verification log,
so it cannot run without both. When one is missing the member can't fix it, so they get a plain
explanation and the staff get a notice naming what to set, instead of the member seeing an
"unknown error".
"""
import logging

import discord
from discord_py_utilities.permissions import find_first_accessible_text_channel

from classes.permissions_notice import PermissionNotice
from databases.transactions.ConfigData import ConfigData
from resources.data.config_variables import config_title

# Config keys verification can't run without.
VERIFICATION_CHANNEL_KEYS = ("approval_channel", "verification_failure_log")


class VerificationNotSetUp(Exception) :
	"""Raised when the server is missing channels verification needs."""

	def __init__(self, missing: list[str]) :
		self.missing = missing
		super().__init__(f"Verification is not set up, missing: {', '.join(missing)}")


def missing_verification_settings(guild_id: int) -> list[str] :
	"""The config keys from VERIFICATION_CHANNEL_KEYS that are not set for this guild."""
	return [key for key in VERIFICATION_CHANNEL_KEYS if ConfigData().get_key_int_or_zero(guild_id, key) == 0]


def describe_setting(key: str) -> str :
	"""The setting's title plus its config key, so staff can find it in `/config channels`."""
	return f"{config_title(key)} (`{key}`)"


def member_message(missing: list[str]) -> str :
	"""What the member sees: what is wrong and that it is not on them to fix."""
	titles = ", ".join(describe_setting(key) for key in missing)
	return (f"This server hasn't finished setting up Ageverifier (not set: {titles}), so your verification "
	        f"can't be processed yet. The staff have been told; please try again later.")


async def notify_staff(guild: discord.Guild, missing: list[str]) -> bool :
	"""Tell the staff which settings are missing, at most once an hour per guild and problem.

	Goes to the approval channel if it is set, then any channel the bot can post in, then the owner's DMs.
	Never raises, since it is called from exception handlers.
	"""
	try :
		if guild is None or not missing :
			return False
		if not PermissionNotice._should_send(guild.id, f"setup:{','.join(sorted(missing))}") :
			return False
		titles = "\n".join(f"- {describe_setting(key)}" for key in missing)
		message = (f"⚠️ **Ageverifier is not fully set up in {guild.name}**\n"
		           f"A member just tried to verify, but these settings are missing:\n{titles}\n"
		           f"Members can't verify until they are set. Set them with `/config channels` or on the dashboard.")

		targets = []
		mod_channel = guild.get_channel_or_thread(ConfigData().get_key_int_or_zero(guild.id, "approval_channel"))
		if mod_channel is not None :
			targets.append(mod_channel)
		accessible = find_first_accessible_text_channel(guild)
		if accessible is not None and accessible not in targets :
			targets.append(accessible)
		if guild.owner is not None :
			targets.append(guild.owner)

		for target in targets :
			try :
				await target.send(content=message)
				logging.info(f"Sent setup notice to {getattr(target, 'name', target)} in {guild.name} ({guild.id}).")
				return True
			except (discord.Forbidden, discord.HTTPException) as e :
				logging.debug(f"Setup notice delivery to {target} failed: {e}")
		logging.info(f"Could not deliver setup notice for {guild.name} ({guild.id}); no reachable target.")
		return False
	except Exception as e :
		logging.error(f"Failed to send setup notice for guild {getattr(guild, 'id', '?')}: {e}", exc_info=True)
		return False
