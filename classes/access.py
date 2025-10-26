import logging
import os
from datetime import UTC, datetime

import discord
from discord import app_commands

from classes.jsonmaker import Configer
# from classes.databaseController import StaffDbTransactions
from classes.singleton import singleton
from databases.controllers.ServerTransactions import ServerTransactions


class AccessControl(metaclass=singleton) :
	staff: dict = {

	}

	premium_guilds: list[int] = []

	def __init__(self) :
		self.add_staff_to_dict()

	def reload(self) :
		self.add_staff_to_dict()
		self.add_premium_guilds_to_list()

	def add_staff_to_dict(self) :
		self.staff = {}
		# staff_members = StaffDbTransactions().get_all()
		staff_members= []
		for staff in staff_members :
			role = staff.role.lower()
			if role in self.staff :
				self.staff[role].append(staff.uid)
				continue
			self.staff[role] = [staff.uid]
		logging.info("Staff information has been reloaded:")
		logging.info(self.staff)

	def add_premium_guilds_to_list(self):
		self.premium_guilds = []
		guilds = ServerTransactions().get_all(id_only=False)
		for guild in guilds :
			if guild.premium is not None and datetime.now(tz=UTC) < guild.premium :
				self.premium_guilds.append(guild.guild)
		logging.info("Premium guilds have been reloaded")

	def access_owner(self, user_id: int) -> bool :
		return True if user_id == int(os.getenv('OWNER')) else False

	def access_all(self, user_id: int) -> bool :
		return True if user_id in self.staff.get('dev', []) or user_id in self.staff.get('rep', []) else False

	def access_dev(self, user_id: int) -> bool :
		return True if user_id in self.staff.get('dev', []) else False

	def check_access(self, role="") :
		def pred(interaction: discord.Interaction) -> bool:
			match role.lower() :
				case "owner" :
					return self.access_owner(interaction.user.id)
				case "dev" :
					return self.access_dev(interaction.user.id)
				case _ :
					return self.access_all(interaction.user.id)
		return app_commands.check(pred)

	def check_blacklist(self):
		async def pred(interaction: discord.Interaction) -> bool:
			if await Configer.is_user_blacklisted(interaction.user.id):
				return False
			return True

		return app_commands.check(pred)

	def is_premium(self, guild_id: int):
		if os.getenv('DEBUG'):
			logging.info(f"[DEBUG]: {guild_id} checking for premium status in list: {self.premium_guilds}")
		return guild_id in self.premium_guilds