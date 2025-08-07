import logging

from sqlalchemy import Select

from databases import current as db
from databases.controllers.ConfigData import ConfigData
from databases.controllers.ConfigTransactions import ConfigTransactions
from databases.controllers.DatabaseTransactions import DatabaseTransactions
from databases.current import Servers


class ServerTransactions(DatabaseTransactions) :

	def add(self, guildid: int, active: bool = True, reload=True) -> Servers :
		guild = self.get(guildid)
		if guild is not None :
			self.update(guildid, active)
			ConfigTransactions().toggle_add(guildid, "AUTOKICK")
			ConfigTransactions().toggle_add(guildid, "AUTOMATIC")
			ConfigTransactions().toggle_add(guildid, "WELCOME", "ENABLED")
			ConfigTransactions().toggle_add(guildid, "UPDATEROLES")
			ConfigTransactions().toggle_add(guildid, "PINGOWNER")
			ConfigTransactions().config_unique_add(guildid, "COOLDOWN", 5)
			return guild
		with self.createsession() as session :
			g = db.Servers(guild=guildid, active=active)
			session.merge(g)
			self.commit(session)
		ConfigTransactions().toggle_add(guildid, "AUTOKICK")
		ConfigTransactions().toggle_add(guildid, "AUTOMATIC")
		ConfigTransactions().toggle_add(guildid, "WELCOME", "ENABLED")
		ConfigTransactions().toggle_add(guildid, "LOBBYWELCOME", "ENABLED")
		ConfigTransactions().toggle_add(guildid, "UPDATEROLES", )
		ConfigTransactions().toggle_add(guildid, "PINGOWNER")

		ConfigTransactions().config_unique_add(guildid, "COOLDOWN", 5)
		if reload :
			ConfigData().load_guild(guildid)
		return g

	def get_all(self, id_only=True) :
		with self.createsession() as session :
			if id_only is False :
				return session.query(Servers).all()
			return [sid[0] for sid in session.query(Servers.guild).all()]

	def get(self, guild_id: int, session=None) :
		if session:
			return session.scalar(Select(Servers).where(Servers.guild == guild_id))
		with self.createsession() as session :
			return session.scalar(Select(Servers).where(Servers.guild == guild_id))

	def update(self, guild_id: int, active: bool = None, reload=True) :
		with self.createsession() as session :
			guild = self.get(guild_id, session=session)
			if not guild :
				return False
			updated_data = {
				"active" : active
			}
			for field, value in updated_data.items() :
				setattr(guild, field, value)
				logging.info(f"Updated {guild.guild} with:")
				logging.info(updated_data)
				self.commit(session)
				if reload :
					ConfigData().load_guild(guild_id)
			return True
