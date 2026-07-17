import datetime
import logging

import discord
from sqlalchemy import Select, or_

from databases.current import Config, Servers
from databases.transactions.ConfigTransactions import ConfigTransactions
from databases.transactions.DatabaseTransactions import DatabaseTransactions
from databases.transactions.UserTransactions import UserTransactions
from resources.data.config_variables import VERIFICATION_KEY, VerificationMethods, available_toggles, enabled_toggles, \
	lobby_approval_toggles


class ServerTransactions(DatabaseTransactions) :

	def add(self, guildid: int, active: bool = True, name: str = "", owner: discord.Member = None, member_count: int = 0,
	        invite: str = "", reload=True, invite_date=None) :
		with self.createsession() as session :

			guild = self.get(guildid, session=session)
			owner_name = owner.name if owner else ""
			owner_id = owner.id if owner else 0
			owner = UserTransactions().user_exists(owner_id)
			if not owner :
				UserTransactions().add_user_empty(owner_id)

			if guild is not None :
				if invite == "" :
					invite = None
				self.update(guildid, active, name, owner_name, member_count, invite,
				            owner_id=owner_id if owner_id != 0 else None, invite_date=invite_date, )
			else :
				session = self.createsession()
				g = Servers(
					guild=guildid,
					active=active,
					name=name,
					owner=owner_name,
					member_count=member_count,
					invite=invite,
					invite_date=invite_date,
					owner_id=owner_id,
				)
				session.merge(g)
				self.commit(session)
				guild = g

				# Apply default configuration — ONLY for brand-new servers.
				# Backfilling newly-introduced config keys to already-existing guilds
				# is handled in bulk by backfill_config() (run from the daily
				# sync_configs task), so this no longer runs for every guild on every
				# hourly sync.
				for toggle in available_toggles + list(lobby_approval_toggles.keys()) :
					if toggle.upper() in enabled_toggles :
						ConfigTransactions().toggle_add(guildid, toggle, "ENABLED")
					ConfigTransactions().toggle_add(guildid, toggle)
				ConfigTransactions().config_unique_add(guildid, "COOLDOWN", 5)
				ConfigTransactions().config_unique_add(guildid, VERIFICATION_KEY, VerificationMethods.BASIC)

		if reload :
			from databases.transactions.ConfigData import ConfigData
			ConfigData().load_guild(guildid)

		return guild

	def get_all(self, id_only=True) :
		with self.createsession() as session :
			if not id_only :
				return session.query(Servers).all()
			return [sid[0] for sid in session.query(Servers.guild).all()]

	def backfill_config(self) :
		"""Ensures every guild has every currently-defined default config key.

		This does the same "insert missing keys only" work that add()'s per-guild
		seeding loop used to do on every sync, but in bulk: one SELECT of all
		existing (guild, key) pairs plus a single bulk INSERT of whatever is
		missing — instead of one existence check per (guild, key). Existing values
		are never overwritten, so a guild that changed a toggle keeps its choice.

		Returns the number of config rows inserted.
		"""
		# Same desired set that add() seeds for a new server.
		desired_toggles = list(available_toggles) + list(lobby_approval_toggles.keys())
		unique_defaults = [("COOLDOWN", "5"), (VERIFICATION_KEY, str(VerificationMethods.BASIC))]

		with self.createsession() as session :
			# Every (guild, key) that already exists — one query for the whole table.
			existing = {
				(guild, key) for guild, key in session.execute(Select(Config.guild, Config.key)).all()
			}
			guild_ids = [gid for (gid,) in session.execute(Select(Servers.guild)).all()]

			rows = []
			for gid in guild_ids :
				for toggle in desired_toggles :
					key = toggle.upper()
					if (gid, key) not in existing :
						rows.append({
							"guild" : gid,
							"key"   : key,
							"value" : "ENABLED" if toggle.upper() in enabled_toggles else "DISABLED",
						})
				for key, value in unique_defaults :
					if (gid, key.upper()) not in existing :
						rows.append({"guild" : gid, "key" : key.upper(), "value" : value})

			if not rows :
				logging.info("Config backfill: all guilds already up to date, nothing to insert.")
				return 0

			session.bulk_insert_mappings(Config, rows)
			self.commit(session)
			logging.info(f"Config backfill: inserted {len(rows)} missing config rows across {len(guild_ids)} guilds.")
			return len(rows)

	def get(self, guild_id: int, session=None) -> "Servers" :
		if session :
			return session.scalar(Select(Servers).where(Servers.guild == guild_id))
		with self.createsession() as session :
			return session.scalar(Select(Servers).where(Servers.guild == guild_id))

	def update(self, guild_id: int, active: bool = None, name: str = None, owner: str = None, member_count: int = None,
	           invite: str = None, premium: datetime = None, owner_id=None, reload=True, invite_date=None) -> bool :

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
				"invite_date"  : invite_date,
				"premium"      : premium,
				"owner_id"     : owner_id,
				"updated_at" : datetime.datetime.now()
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

	def get_invalid_invites(self) :
		with (self.createsession() as session) :
			# calculate cutoff date
			cutoff = datetime.datetime.now() - datetime.timedelta(days=7)
			# Select servers with invites older than 6 days.
			return session.query(Servers).filter(or_(Servers.invite.is_(None),
			                                         Servers.invite == '',
			                                         Servers.invite_date < cutoff)).all()
