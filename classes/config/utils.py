import logging
from abc import ABC, abstractmethod

import discord

from discord_py_utilities.messages import send_message
from databases.transactions.ConfigData import ConfigData


class ConfigUtils(ABC):

	@staticmethod
	@abstractmethod
	async def log_change(guild:discord.Guild, changes: dict, user_name: str = None, channel: discord.TextChannel = None) :
		guild_id = guild.id
		logging.info(f"Configuration changed in guild {guild_id}: {changes} by user {user_name}")
		if not ConfigData().get_toggle(guild_id, "logchanges") :
			logging.info("Logging of configuration changes is disabled.")
			return
		logging.info("Logging of configuration changes is enabled.")
		if not channel:
			modlobby = ConfigData().get_key_int_or_zero(guild_id, "lobbymod")
			channel = guild.get_channel(modlobby)
		if channel is None :
			logging.info("No modlobby channel found for logging configuration changes.")
			return
		await send_message(channel,
		                   f"[CONFIG CHANGE] {user_name} changed the configuration:\n"
		                            f"```{'\n'.join([f'{key}: {value if value else 'This key was removed'}' for key, value in changes.items()])}```\n-# this setting can be turned off with `/config toggles key:logchanges action:disabled`",
		                    error_mode='ignore'
		                   )

