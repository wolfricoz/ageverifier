import datetime
import json
import logging
import os
from datetime import datetime as dt
from databases.controllers.AgeRoleTransactions import AgeRoleTransactions
from classes.singleton import singleton
from databases.controllers.ConfigTransactions import ConfigTransactions
from databases.exceptions.ConfigNotFound import ConfigNotFound
from databases.exceptions.KeyNotFound import KeyNotFound


class ConfigData(metaclass=singleton) :
	"""
	The goal of this class is to save the config to reduce database calls for the config; especially the roles.
	"""
	conf = {}

	def __init__(self) :
		pass

	def reload(self) :
		"""

		"""
		logging.info("reloading config")
		for guild_id in self.conf :
			self.load_guild(guild_id)
		# logging.debug(self.conf)

	async def load_all_guilds(self):
		start = dt.now()
		from databases.controllers.ServerTransactions import ServerTransactions
		logging.info("Loading all guild configurations")
		server_ids = ServerTransactions().get_all(id_only=True)
		for server_id in server_ids :
			server_start = dt.now()
			self.load_guild(server_id)
			logging.info(f"Loaded guild {server_id} in {dt.now() - server_start}")
		logging.info(f"Loaded all guild configurations in {dt.now() - start}")

	def load_guild(self, guild_id: int) :
		"""

		:param guild_id: 
		"""
		config = ConfigTransactions().server_config_get(guild_id)
		settings = config
		add_list = ['REM', "RETURN", "JOIN", "EXCLUDE"]
		add_dict = ["SEARCH", "BAN", "ADD"]
		self.conf[guild_id] = {}
		reload = False

		for key in add_list :
			self.conf[guild_id][key] = []
		role = AgeRoleTransactions().get_all(guild_id)
		for key in add_dict :
			self.conf[guild_id][key] = {}

		for x in settings :
			if x.key in ["ADD"] :
				AgeRoleTransactions().add(guild_id, x.value, "ADD", reload=False)
				ConfigTransactions().config_unique_remove(guild_id, x.key)
				reload = True
				continue
			if x.key in add_list :
				self.conf[guild_id][x.key].append(int(x.value))
				continue
			if x.key.upper().startswith("SEARCH") :
				self.conf[guild_id]["SEARCH"][x.key.replace('SEARCH-', '')] = x.value
				continue
			if x.key.upper().startswith("BAN") :
				self.conf[guild_id]["BAN"][x.key.replace('BAN-', '')] = x.value
				continue
			self.conf[guild_id][x.key] = x.value
		for x in role :
			self.conf[guild_id]['ADD'][x.role_id] = {
				"MAX" : x.maximum_age,
				"MIN" : x.minimum_age,
			}
		if reload :
			self.load_guild(guild_id)
		self.output_to_json()

	def get_config(self, guildid) :
		"""

		:param guildid: 
		:return: 
		"""
		try :
			return self.conf[guildid]
		except KeyError :
			raise ConfigNotFound

	def get_key_int(self, guildid: int, key: str) :
		"""

		:param guildid: 
		:param key: 
		:return: 
		"""
		try :
			return int(self.conf[guildid][key.upper()])
		except KeyError :
			raise KeyNotFound(key.upper())

	def get_key_int_or_zero(self, guildid: int, key: str) :
		"""

		:param guildid: 
		:param key: 
		:return: 
		"""
		if guildid not in self.conf :
			return 0
		if key.upper() not in self.conf[guildid] :
			return 0

		result = self.conf[guildid].get(key.upper(), 0)
		if isinstance(result, int) :
			return result
		if result is None:
			logging.warning(f"{guildid} key {key} is not an int")
			return 0
		if isinstance(result, str) :
			return int(result)

		return result
	
	def get_toggle(self, guildid: int, key: str, expected: str = "ENABLED", default: str = "DISABLED") -> bool:
		"""
		:param guildid: 
		:param key: 
		:param expected: 
		:param default: 
		:return: 
		"""
		return str(ConfigData().get_key(guildid, key, default)).upper() == expected.upper()

	def get_key(self, guildid: int, key: str, default=None) :
		try :
			return self.conf[guildid][key.upper()]

		except KeyError :
			if default:
				return default
			raise KeyNotFound(key.upper())

	def get_key_or_none(self, guildid: int, key: str) :
		"""

		:param guildid: 
		:param key: 
		:return: 
		"""
		return self.conf[guildid].get(key.upper(), None)

	def output_to_json(self)  -> None:
		"""This is for debugging only.
		:rtype: None
		"""
		if not os.path.isdir('debug') :
			os.mkdir('debug')
		with open('debug/config.json', 'w') as f :
			json.dump(self.conf, f, indent=4)
