import logging
from abc import ABC, abstractmethod

import discord

from databases.transactions.ConfigData import ConfigData
from resources.data.config_variables import channelchoices, config_title, rolechoices


def is_unset(value) -> bool :
	# Unset channels are sometimes stored as the literal string "None" (AGEVERIFIER-GY).
	return value is None or value == [] or (isinstance(value, str) and value.strip() in ("", "None"))


def format_config_value(key: str, value) -> str :
	"""A config value as staff should read it: channels and roles as mentions instead of raw ids.
	Send the result with AllowedMentions.none(), or a role mention pings the role."""
	if is_unset(value) :
		return "not set"
	kind = "channel" if key.lower() in channelchoices else "role" if key.lower() in rolechoices else None
	if kind is None :
		return str(value)
	ids = value if isinstance(value, list) else [value]
	mentions = []
	for item in ids :
		try :
			mentions.append(f"<#{int(item)}>" if kind == "channel" else f"<@&{int(item)}>")
		except (TypeError, ValueError) :
			mentions.append(str(item))
	return ", ".join(mentions)


class ConfigUtils(ABC):

	@staticmethod
	@abstractmethod
	async def log_change(guild:discord.Guild, changes: dict, user_name: str = None, channel: discord.TextChannel = None) :
		guild_id = guild.id
		logging.info(f"Configuration changed in guild {guild_id}: {changes} by user {user_name}")
		if not ConfigData().get_toggle(guild_id, "log_config_changes") :
			logging.info("Logging of configuration changes is disabled.")
			return
		logging.info("Logging of configuration changes is enabled.")
		if not channel:
			modlobby = ConfigData().get_key_int_or_zero(guild_id, "approval_channel")
			channel = guild.get_channel(modlobby)
		if channel is None :
			logging.info("No modlobby channel found for logging configuration changes.")
			return
		lines = [f"- **{config_title(key)}**: {format_config_value(key, value) if not is_unset(value) else 'removed'}"
		         for key, value in changes.items()]
		text = (f"[CONFIG CHANGE] {user_name} changed the configuration:\n" + "\n".join(lines))[:1900]
		text += "\n-# this setting can be turned off with `/config toggles key:LOG_CONFIG_CHANGES action:disabled`"
		try :
			# Mentions only make the values readable; nobody should be pinged by a config log.
			await channel.send(text, allowed_mentions=discord.AllowedMentions.none())
		except discord.HTTPException as e :
			logging.info(f"Could not post the config change log in {guild_id}: {e}")
