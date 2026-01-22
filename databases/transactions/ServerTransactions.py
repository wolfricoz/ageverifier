import datetime
import logging

import discord
from sqlalchemy import Select

from databases.current import Servers
from databases.transactions.ConfigTransactions import ConfigTransactions
from databases.transactions.DatabaseTransactions import DatabaseTransactions
from databases.transactions.UserTransactions import UserTransactions
from resources.data.config_variables import available_toggles, enabled_toggles, lobby_approval_toggles


class ServerTransactions(DatabaseTransactions) :

	def add(self, guildid: int, active: bool = True, name: str = "", owner: discord.Member = None, member_count: int = 0,
	        invite: str = "", reload=True) :
		with self.createsession() as session :

			guild = self.get(guildid, session=session)
			owner_name = owner.name if owner else ""
			owner_id = owner.id if owner else 0
			owner = UserTransactions().user_exists(owner_id)
			if not owner and owner_id != 0 :
				UserTransactions().add_user_empty(owner_id)

			if guild is not None :

				self.update(guildid, active, name, owner_name, member_count, invite, owner_id=owner_id if owner_id != 0 else None)
			else :
				session = self.createsession()
				g = Servers(
					guild=guildid,
					active=active,
					name=name,
					owner=owner_name,
					member_count=member_count,
					invite=invite,
					owner_id=owner_id,
				)
				session.merge(g)
				self.commit(session)
				guild = g

			# Apply configurations to new servers

			for toggle in available_toggles + list(lobby_approval_toggles.keys()):
				if toggle.upper() in enabled_toggles:
					ConfigTransactions().toggle_add(guildid, toggle, "ENABLED")
				ConfigTransactions().toggle_add(guildid, toggle)
			ConfigTransactions().config_unique_add(guildid, "COOLDOWN", 5)

		if reload :
			from databases.transactions.ConfigData import ConfigData
			ConfigData().load_guild(guildid)

		return guild

	def get_all(self, id_only=True) :
		with self.createsession() as session :
			if not id_only :
				return session.query(Servers).all()
			return [sid[0] for sid in session.query(Servers.guild).all()]

	def get(self, guild_id: int, session=None)  -> "Servers"  :
		if session :
			return session.scalar(Select(Servers).where(Servers.guild == guild_id))
		with self.createsession() as session :
			return session.scalar(Select(Servers).where(Servers.guild == guild_id))

	def update(self, guild_id: int, active: bool = None, name: str = None, owner: str = None, member_count: int = None,
	           invite: str = None, premium: datetime = None, owner_id=None, reload=True) -> bool :

		with self.createsession() as session :
			guild = self.get(guild_id, session=session)
			if not guild :
				return False

			updated_data = {
				"active"       : active,
				"name"         : name,
				"owner"        : owner,
				"member_count" : member_count,
				"invite"       : invite,
				"premium"      : premium,
				"owner_id"     : owner_id
			}

			# Filter out None values to perform partial updates
			data_to_update = {k : v for k, v in updated_data.items() if v is not None}

			if not data_to_update :
				logging.info(f"No new data provided for server {guild_id}, no changes made.")
				return True

			for field, value in data_to_update.items() :
				setattr(guild, field, value)

			logging.info(f"Updated server {guild.guild} with:")
			logging.info(data_to_update)

			self.commit(session)

			if reload :
				from databases.transactions.ConfigData import ConfigData

				ConfigData().load_guild(guild_id)

			return True

	def delete(self, guild_id: int) :
		with self.createsession() as session :
			guild = self.get(guild_id, session=session)
			if not guild :
				return False
			session.delete(guild)
			self.commit(session)
			return True

	def delete_all_user(self, user_id: int, only_delete_owner: bool = False) :
		with self.createsession() as session :
			if only_delete_owner :
				guilds = session.query(Servers).filter(Servers.owner_id == user_id).all()
				for guild in guilds :
					guild.owner_id = None
				self.commit(session)
				return True


			guilds = session.query(Servers).filter(Servers.owner_id == user_id).all()
			for guild in guilds :
				session.delete(guild)
			self.commit(session)
			return True