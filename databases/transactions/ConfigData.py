import asyncio
import json
import logging
import os

import discord
from discord import CategoryChannel, ForumChannel, StageChannel, TextChannel, Thread, VoiceChannel
from discord_py_utilities.messages import send_message

from classes.singleton import Singleton
from databases.exceptions.ConfigNotFound import ConfigNotFound
from databases.exceptions.KeyNotFound import KeyNotFound
from databases.transactions.AgeRoleTransactions import AgeRoleTransactions
from databases.transactions.ConfigTransactions import ConfigTransactions


class ConfigData(metaclass=Singleton) :
	"""
	The goal of this class is to save the config to reduce database calls for the config; especially the roles.
	"""
	conf = {}
	reloading = False

	def __init__(self) :
		pass

	async def reload(self) :
		"""

		"""
		logging.info("reloading config")
		if self.reloading :
			return
		self.reloading = True
		for guild_id in self.conf :
			await asyncio.sleep(0.001)
			self.load_guild(guild_id)
		self.reloading = False

	# logging.debug(self.conf)

	async def load_all_guilds(self) :
		logging.info(f"Loading all guilds")
		# Regardless if the guild exists, we add it to the config to avoid KeyErrors

		# Fetch the settings from the database
		items = ConfigTransactions().server_config_all()
		for item in items:
			await asyncio.sleep(0)
			guild_id = item.guild

			self.conf[guild_id] = {}

			add_list = ["VERIFICATION_REMOVE_ROLE", "RETURN_REMOVE_ROLE", "SERVER_JOIN_ROLE", "AUTO_UPDATE_EXCLUDED_ROLES",
			            "REVERIFICATION_ROLE"]
			add_dict = ["VERIFICATION_ADD_ROLE"]

			for key in add_list :
				self.conf[guild_id][key] = []



			for key in add_dict :
				self.conf[guild_id][key] = {}

			conf_key = item.key.upper()

			if conf_key in ["VERIFICATION_ADD_ROLE"] :
				AgeRoleTransactions().add(guild_id, item.value, "VERIFICATION_ADD_ROLE", reload=False)
				ConfigTransactions().config_unique_remove(guild_id, item.key)
				continue

			if conf_key in add_list :
				self.conf[guild_id][conf_key].append(int(item.value))
				continue

			self.conf[guild_id][conf_key] = item.value

		# Moved to it doesn't run during every config item
		ageroles = AgeRoleTransactions().get_all()
		for x in ageroles :
			self.conf[x.guild_id]["VERIFICATION_ADD_ROLE"][x.role_id] = {
				"MAX" : x.maximum_age,
				"MIN" : x.minimum_age,
			}


		self.output_to_json()



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
		# Regardless if the guild exists, we add it to the config to avoid KeyErrors
		self.conf[guild_id] = {}

		# Fetch the settings from the database
		config = ConfigTransactions().server_config_get(guild_id)
		settings = config
		add_list = ["VERIFICATION_REMOVE_ROLE", "RETURN_REMOVE_ROLE", "SERVER_JOIN_ROLE", "AUTO_UPDATE_EXCLUDED_ROLES",
		            "REVERIFICATION_ROLE"]
		add_dict = ["VERIFICATION_ADD_ROLE"]
		reload = False

		for key in add_list :
			self.conf[guild_id][key] = []
		role = AgeRoleTransactions().get_all_guild(guild_id)
		for key in add_dict :
			self.conf[guild_id][key] = {}

		for x in settings :
			conf_key = x.key.upper()
			if conf_key in ["VERIFICATION_ADD_ROLE"] :
				AgeRoleTransactions().add(guild_id, x.value, "VERIFICATION_ADD_ROLE", reload=False)
				ConfigTransactions().config_unique_remove(guild_id, x.key)
				reload = True
				continue
			if conf_key in add_list :
				self.conf[guild_id][conf_key].append(int(x.value))
				continue
			self.conf[guild_id][conf_key] = x.value
		for x in role :
			self.conf[guild_id]["VERIFICATION_ADD_ROLE"][x.role_id] = {
				"MAX" : x.maximum_age,
				"MIN" : x.minimum_age,
			}
		if reload :
			self.load_guild(guild_id)
		self.output_to_json()

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

	async def get_channel(self, guild: discord.Guild,
	                      channel_type: str = "modchannel") -> None | VoiceChannel | StageChannel | ForumChannel | TextChannel | CategoryChannel | Thread :
		"""Gets the channel from the config"""
		channel_id = self.get_key_or_none(guild.id, channel_type)
		if not isinstance(channel_id, int) :

			if isinstance(channel_id, str) and channel_id.isnumeric() :
				channel_id = int(channel_id)
			else :
				channel_id = None

		if channel_id is None :
			await send_message(guild.owner,
			                   f"No `{channel_type}` channel set for {guild.name}, please set it up using the /config command")
			return None
		channel = guild.get_channel(channel_id)
		if channel is None :
			attempts = 0
			while attempts < 3 and channel is None :
				try :
					channel = await guild.fetch_channel(channel_id)
				except discord.NotFound :
					channel = None
					continue
		if channel is None :
			await send_message(guild.owner,
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
