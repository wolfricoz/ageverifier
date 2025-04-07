import logging
from datetime import datetime, timedelta

from classes.singleton import singleton


class LobbyTimers(metaclass=singleton):

	cooldowns = {

	}

	def add_cooldown(self, guild_id: int, user_id: int, duration: int) -> None:
		"""Sets a cooldown for a user in a guild, duration is in minutes"""
		if duration < 1:
			return
		if guild_id not in self.cooldowns:
			self.cooldowns[guild_id] = {}
		self.cooldowns[guild_id][user_id] = datetime.now() + timedelta(minutes=duration)
		logging.debug(f"Added cooldown for {user_id} in {guild_id} for {duration} minutes")

	def check_cooldown(self, guild_id: int, user_id: int) -> bool | datetime:
		"""Checks if a user is on cooldown in a guild"""
		if guild_id not in self.cooldowns:
			return False
		if user_id not in self.cooldowns[guild_id]:
			return False
		if datetime.now() > self.cooldowns[guild_id][user_id]:
			del self.cooldowns[guild_id][user_id]
			return False
		return self.cooldowns[guild_id][user_id]

