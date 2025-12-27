import logging

import sqlalchemy.exc
from sqlalchemy import Select

from databases import current as db
from databases.transactions.DatabaseTransactions import DatabaseTransactions
from databases.current import Config, Servers


class ConfigTransactions(DatabaseTransactions) :

	def config_unique_add(self, guildid: int, key: str, value, overwrite=False) :
		# This function should check if the item already exists, if so it will override it or throw an error.
		with self.createsession() as session :
			# Check if guild exists
			from databases.transactions.ServerTransactions import ServerTransactions
			db_guild = ServerTransactions().get(guildid)
			if not db_guild :
				ServerTransactions().add(guildid, active=True, name="fetch error", owner=None, member_count=0, invite="")
			# create the config item
			try:
				value = str(value)
				if ConfigTransactions().key_exists_check(guildid, key, overwrite) is True and overwrite is False :
					return False
				if ConfigTransactions().key_exists_check(guildid, key, overwrite) :
					entries = session.scalars(
						Select(db.Config).where(db.Config.guild == guildid, db.Config.key == key.upper())).all()
					for entry in entries :
						session.delete(entry)
				item = db.Config(guild=guildid, key=key.upper(), value=value)
				session.add(item)
				self.commit(session)
				self.reload_guild(guildid)
				logging.info(f"Adding unique key with data: {guildid}, {key}, {value}, and overwrite {overwrite}")
				return True
			except sqlalchemy.exc.PendingRollbackError:
				logging.error("Pending rollback error occurred, rolling back session.")
				session.rollback()
				session.close()
				return False


	def toggle(self, guildid: int, key: str, value) :
		# This function should check if the item already exists, if so it will override it or throw an error.
		with self.createsession() as session :
			value = str(value)
			guilddata = session.scalar(Select(Config).where(Config.guild == guildid, Config.key == key.upper()))
			if guilddata is None :
				ConfigTransactions().config_unique_add(guildid, key, value, overwrite=True)
				return False
			guilddata.value = value
			self.commit(session)
			self.reload_guild(guildid)
			return True


	def config_unique_get(self, guildid: int, key: str) :
		with self.createsession() as session :
			if not ConfigTransactions().key_exists_check(guildid, key) :
				return False
			exists = session.scalar(Select(db.Config).where(db.Config.guild == guildid, db.Config.key == key.upper()))
			return exists


	def config_key_add(self, guildid: int, key: str, value, overwrite) :
		with self.createsession() as session :
			value = str(value)
			if ConfigTransactions().key_multiple_exists_check(guildid, key, value) :
				return False
			item = db.Config(guild=guildid, key=key.upper(), value=value)
			session.add(item)
			self.commit(session)
			self.reload_guild(guildid)
			return True


	def key_multiple_exists_check(self, guildid: int, key: str, value) :
		with self.createsession() as session :
			exists = session.scalar(
				Select(db.Config).where(db.Config.guild == guildid, db.Config.key == key, db.Config.value == value))
			session.close()
			if exists is not None :
				return True
			return False


	def config_key_remove(self, guildid: int, key: str, value) :
		with self.createsession() as session :
			if not ConfigTransactions().key_multiple_exists_check(guildid, key, value) :
				return False
			exists = session.scalar(
				Select(db.Config).where(db.Config.guild == guildid, db.Config.key == key, db.Config.value == value))
			session.delete(exists)
			self.commit(session)
			self.reload_guild(guildid)
			return None


	def config_unique_remove(self, guild_id: int, key: str) :
		with self.createsession() as session :
			if not ConfigTransactions().key_exists_check(guild_id, key) :
				return False
			exists = session.scalar(
				Select(db.Config).where(db.Config.guild == guild_id, db.Config.key == key))
			if exists is None :
				return False
			session.delete(exists)
			self.commit(session)
			return None


	def key_exists_check(self, guildid: int, key: str, overwrite=False) :
		with self.createsession() as session :

			exists = session.scalar(
				Select(db.Config).where(db.Config.guild == guildid, db.Config.key == key.upper()))
			if exists is None :
				session.close()
				return False
			if not overwrite :
				return True
			session.delete(exists)
			self.commit(session)
			return True


	def toggle_add(self, guildid: int, key: str, value="DISABLED") :
		with self.createsession() as session :
			key = key.upper()
			if ConfigTransactions().key_exists_check(guildid, key) :
				return
			toggle = Config(guild=guildid, key=key, value=value)
			session.merge(toggle)
			logging.info(f"Added toggle '{key}' with value '{value}' in {guildid}")
			self.commit(session)


	def server_config_get(self, guildid) :
		with self.createsession() as session :
			return session.scalars(Select(db.Config).where(db.Config.guild == guildid)).all()
