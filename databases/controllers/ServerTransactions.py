import logging

from sqlalchemy import Select

from databases.controllers.ConfigData import ConfigData
from databases.controllers.ConfigTransactions import ConfigTransactions
from databases.controllers.DatabaseTransactions import DatabaseTransactions
from databases.current import Servers


class ServerTransactions(DatabaseTransactions) :

	def add(self, guildid: int, active: bool = True, name: str = "", owner: str = "", member_count: int = 0,
	        invite: str = "", premium: bool = False, reload=True) -> "Servers" :
		with self.createsession() as session:

			guild = self.get(guildid, session=session)

			if guild is not None :

				self.update(guildid, active, name, owner, member_count, invite, premium)
			else :
				session = self.createsession()
				g = Servers(
					guild=guildid,
					active=active,
					name=name,
					owner=owner,
					member_count=member_count,
					invite=invite,
					premium=premium
				)
				session.merge(g)
				self.commit(session)
				guild = g

			# Apply configurations to new servers
			ConfigTransactions().toggle_add(guildid, "AUTOKICK")
			ConfigTransactions().toggle_add(guildid, "AUTOMATIC")
			ConfigTransactions().toggle_add(guildid, "WELCOME", "ENABLED")
			ConfigTransactions().toggle_add(guildid, "LOBBYWELCOME", "ENABLED")
			ConfigTransactions().toggle_add(guildid, "UPDATEROLES")
			ConfigTransactions().toggle_add(guildid, "LEGACY_MESSAGE")
			ConfigTransactions().toggle_add(guildid, "BANS", "ENABLED")
			ConfigTransactions().toggle_add(guildid, "JOINED_AT", "ENABLED")
			ConfigTransactions().toggle_add(guildid, "CREATED_AT", "ENABLED")
			ConfigTransactions().toggle_add(guildid, "USER_ID", "ENABLED")
			ConfigTransactions().toggle_add(guildid, "PICTURE_LARGE")
			ConfigTransactions().toggle_add(guildid, "PICTURE_SMALL", "ENABLED")
			ConfigTransactions().toggle_add(guildid, "SHOW_INLINE")
			ConfigTransactions().config_unique_add(guildid, "COOLDOWN", 5)

		if reload :
			ConfigData().load_guild(guildid)

		return guild

	def get_all(self, id_only=True) :
		with self.createsession() as session :
			if id_only is False :
				return session.query(Servers).all()
			return [sid[0] for sid in session.query(Servers.guild).all()]

	def get(self, guild_id: int, session=None) :
		if session :
			return session.scalar(Select(Servers).where(Servers.guild == guild_id))
		with self.createsession() as session :
			return session.scalar(Select(Servers).where(Servers.guild == guild_id))

	def update(self, guild_id: int, active: bool = None, name: str = None, owner: str = None, member_count: int = None,
	           invite: str = None, premium: bool = None, reload=True) -> bool :

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
				"premium"      : premium
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

