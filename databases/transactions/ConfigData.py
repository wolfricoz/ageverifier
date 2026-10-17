import asyncio
import json
import logging
import os
from collections import defaultdict
from typing import Iterable

import discord
from discord import CategoryChannel, ForumChannel, StageChannel, TextChannel, Thread, VoiceChannel
from discord_py_utilities.messages import send_message

from classes.singleton import Singleton
from databases.exceptions.ConfigNotFound import ConfigNotFound
from databases.exceptions.KeyNotFound import KeyNotFound
from databases.transactions.AgeRoleTransactions import AgeRoleTransactions
from databases.transactions.ConfigTransactions import ConfigTransactions

# Config keys that can be stored more than once per guild; they are cached as a list of ids.
LIST_KEYS = ["VERIFICATION_REMOVE_ROLE", "RETURN_REMOVE_ROLE", "SERVER_JOIN_ROLE", "AUTO_UPDATE_EXCLUDED_ROLES",
             "REVERIFICATION_ROLE"]


class ConfigData(metaclass=Singleton) :
	"""
	The goal of this class is to save the config to reduce database calls for the config; especially the roles.
	"""
	conf = {}
	reloading = False
	# Guilds loaded one by one while load_all_guilds was reading; they get loaded again after the swap.
	changed_during_reload = set()

	def __init__(self) :
		pass

	async def reload(self) :
		"""Reloads every guild that is cached right now."""
		await self.load_all_guilds(list(self.conf))

	async def load_all_guilds(self, guild_ids: Iterable[int]) :
		"""Loads the config of all these guilds with two queries and swaps it in as a whole.

		Guilds without config rows get the same empty config load_guild gives them, so they aren't loaded one by one
		later; guilds left out are dropped from the cache. Loading them one by one blocked the event loop for ~40s
		with 770+ guilds and dropped the gateway connection. The queries and building run in a thread.
		"""
		if self.reloading :
			return
		guild_ids = set(guild_ids)
		logging.info(f"Loading config for {len(guild_ids)} guilds")
		self.reloading = True
		self.changed_during_reload = set()
		try :
			conf, legacy = await asyncio.to_thread(self._build_guilds, guild_ids)
			self.conf = conf
		finally :
			self.reloading = False
		# Guilds whose config changed while the thread was reading would otherwise hold stale data until the next reload.
		for guild_id in legacy | (self.changed_during_reload & guild_ids) :
			await asyncio.sleep(0)
			try :
				self.load_guild(guild_id)
			except Exception as e :
				# The bulk-built config stays in place; raising would stop the config_reload loop for good.
				logging.error(f"Could not reload the config of {guild_id} after the bulk load: {e}", exc_info=True)
		logging.info(f"Loaded config for {len(conf)} guilds")

	def _build_guilds(self, guild_ids: set[int]) -> tuple[dict, set[int]] :
		"""Builds the config of these guilds from two queries. Also returns the guilds that still have
		VERIFICATION_ADD_ROLE rows in the config table; load_guild has to move those to the age roles first."""
		settings = defaultdict(list)
		for row in ConfigTransactions().server_config_for(guild_ids) :
			settings[row.guild].append(row)
		roles = defaultdict(list)
		for role in AgeRoleTransactions().get_for_guilds(guild_ids) :
			roles[role.guild_id].append(role)
		legacy = {guild_id for guild_id, rows in settings.items() if
		          any(row.key.upper() == "VERIFICATION_ADD_ROLE" for row in rows)}
		conf = {guild_id : self._build_guild(guild_id, settings[guild_id], roles[guild_id]) for guild_id in guild_ids}
		return conf, legacy

	@staticmethod
	def _build_guild(guild_id: int, settings, roles) -> dict :
		"""Turns a guild's config rows and age roles into its cached config."""
		conf = {key : [] for key in LIST_KEYS}
		conf["VERIFICATION_ADD_ROLE"] = {}
		for x in settings :
			conf_key = x.key.upper()
			if conf_key == "VERIFICATION_ADD_ROLE" :
				continue
			if conf_key in LIST_KEYS :
				try :
					conf[conf_key].append(int(x.value))
				except (TypeError, ValueError) :
					# One bad row would otherwise fail the whole bulk load.
					logging.warning(f"Skipping non-numeric {conf_key} value {x.value!r} in {guild_id}")
				continue
			conf[conf_key] = x.value
		for x in roles :
			conf["VERIFICATION_ADD_ROLE"][x.role_id] = {
				"MAX" : x.maximum_age,
				"MIN" : x.minimum_age,
			}
		return conf

	def cleanup(self) :
		"""

		"""
		self.conf = {}

	def load_guild(self, guild_id: int) :
		"""

		:param guild_id: 
		"""
		logging.info(f"Loading guild {guild_id}")
		print(f"Loading guild {guild_id}")
		if self.reloading :
			self.changed_during_reload.add(guild_id)

		# Fetch the settings from the database
		settings = ConfigTransactions().server_config_get(guild_id)
		# Old servers stored their age roles in the config table; move them to the age roles table.
		moved = False
		for x in settings :
			if x.key.upper() == "VERIFICATION_ADD_ROLE" :
				AgeRoleTransactions().add(guild_id, x.value, "VERIFICATION_ADD_ROLE", reload=False)
				ConfigTransactions().config_unique_remove(guild_id, x.key)
				moved = True
		if moved :
			settings = ConfigTransactions().server_config_get(guild_id)
		# Regardless if the guild exists, we add it to the config to avoid KeyErrors
		self.conf[guild_id] = self._build_guild(guild_id, settings, AgeRoleTransactions().get_all_guild(guild_id))
		# No output_to_json() here: it rewrote the whole cache on every guild load, so a cold cache took
		# ~40s to fill and blocked the gateway heartbeat. config_reload still writes a snapshot before reloading.

	def get_guild(self, guild_id: int) -> dict :
		"""

		:param guild_id:
		:return:
		"""
		if guild_id in self.conf :
			return self.conf[guild_id]
		self.load_guild(guild_id)
		return self.conf[guild_id]

	def get_config(self, guildid) :
		"""

		:param guildid: 
		:return: 
		"""
		try :
			return self.get_guild(guildid)
		except KeyError :
			raise ConfigNotFound

	def get_key_int(self, guildid: int, key: str) :
		"""

		:param guildid: 
		:param key: 
		:return: 
		"""
		try :
			return int(self.get_guild(guildid)[key.upper()])
		except KeyError :
			raise KeyNotFound(key.upper())

	def get_key_int_or_zero(self, guildid: int, key: str) :
		"""

		:param guildid: 
		:param key: 
		:return: 
		"""
		result = self.get_guild(guildid).get(key.upper(), 0)
		if isinstance(result, int) :
			return result
		if result is None or result == "" or result == "None" :
			logging.warning(f"{guildid} key {key} is not an int")
			return 0
		if isinstance(result, str) :
			return int(result)

		return result

	def get_toggle(self, guildid: int, key: str, expected: str = "ENABLED", default: str = "DISABLED") -> bool :
		"""
		:param guildid: 
		:param key: 
		:param expected: 
		:param default: 
		:return: 
		"""
		value = str(self.get_key(guildid, key, default)).upper()

		# Due the database field being a string, it allows for multiple ways to represent enabled/disabled. In legacy we used ENABLED/DISABLED but we're slowly moving to TRUE/FALSE; to ensure backwards compatibility we check for all options we check for all options here.
		if value in ["ENABLED", "TRUE", "1", "ON"] :
			return expected.upper() == "ENABLED"
		if value in ["DISABLED", "FALSE", "0", "OFF"] :
			return expected.upper() == "DISABLED"
		return value == expected.upper()

	def get_key(self, guildid: int, key: str, default=None) :
		try :
			return self.get_guild(guildid)[key.upper()]

		except KeyError :
			if default :
				return default
			raise KeyNotFound(key.upper())

	def get_key_or_none(self, guildid: int, key: str) :
		"""

		:param guildid: 
		:param key: 
		:return: 
		"""
		return self.get_guild(guildid).get(key.upper(), None)

	def get_channel_id(self, guildid: int, key: str) -> int | None :
		"""
		Returns a channel id from the config as an int, or None when it is unset.
		Config values are stored as strings, and unset channels are sometimes stored as the literal
		string "None" or an empty string; int() on those crashed several callers (AGEVERIFIER-E1, AGEVERIFIER-GY).
		:param guildid:
		:param key:
		:return:
		"""
		value = self.get_guild(guildid).get(key.upper(), None)
		if isinstance(value, int) :
			return value
		if isinstance(value, str) and value.strip().isnumeric() :
			return int(value.strip())
		return None

	@staticmethod
	async def _notify_owner(guild: discord.Guild, dedupe_key: str, message: str) -> None :
		"""Tells the guild owner about a config problem. Throttled per guild/key and never raises.

		This used to fire on every call (e.g. every lobby clean up) with error_mode='error'; an owner the bot
		can't DM then crashed discord_py_utilities' permission check on a Member (AGEVERIFIER-EP).
		"""
		# Lazy import: keeps ConfigData importable without pulling in the notice's dependencies at load.
		from classes.permissions_notice import PermissionNotice
		if guild.owner is None or not PermissionNotice._should_send(guild.id, dedupe_key) :
			return
		try :
			await send_message(guild.owner, message, error_mode="ignore")
		except Exception as e :
			logging.info(f"Could not notify the owner of {guild.name}({guild.id}): {e}")

	async def get_channel(self, guild: discord.Guild,
	                      channel_type: str = "modchannel") -> None | VoiceChannel | StageChannel | ForumChannel | TextChannel | CategoryChannel | Thread :
		"""Gets the channel from the config"""
		channel_id = self.get_channel_id(guild.id, channel_type)

		if channel_id is None :
			await self._notify_owner(guild, f"missing-channel:{channel_type}",
			                         f"No `{channel_type}` channel set for {guild.name}, please set it up using the /config command")
			return None
		channel = guild.get_channel_or_thread(channel_id)
		attempts = 0
		# Only Discord-side errors are worth retrying. A deleted or hidden channel will not come back, and
		# retrying it without counting attempts looped until the queue's 600s timeout (AGEVERIFIER-HY and friends).
		while channel is None and attempts < 3 :
			attempts += 1
			try :
				channel = await guild.fetch_channel(channel_id)
			except (discord.NotFound, discord.Forbidden) :
				break
			except discord.DiscordServerError as e :
				logging.info(f"Discord error fetching {channel_type} ({channel_id}) in {guild.name}, attempt {attempts}/3: {e}")
				await asyncio.sleep(attempts)
		if channel is None :
			await self._notify_owner(guild, f"unfetchable-channel:{channel_type}",
			                         f"ageverifier could not fetch the `{channel_type}` channel with id {channel_id} in {guild.name}, please verify it exists and is accessible by the bot. If it does then discord may be having issues.")
			return None
		return channel


	def output_to_json(self) -> None :
		"""This is for debugging only.
		:rtype: None
		"""
		if not os.path.isdir('debug') :
			os.mkdir('debug')
		with open('debug/config.json', 'w') as f :
			json.dump(self.conf, f, indent=4)
