import datetime
import json
import logging
from abc import ABC, abstractmethod
from datetime import timezone

import pymysql.err
import sqlalchemy.exc
from sqlalchemy import and_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy.sql import Select
from sqlalchemy.sql.expression import text

import databases.current as db
from classes.encryption import Encryption
from classes.singleton import singleton
from databases.current import *

session = Session(bind=db.engine, expire_on_commit=False, )


class ConfigNotFound(Exception) :
	"""config item was not found or has not been added yet."""

	def __init__(self, message="guild config has not been loaded yet or has not been created yet.") :
		self.message = message
		super().__init__(self.message)


class CommitError(Exception) :
	"""the commit failed."""

	def __init__(self, message="Commiting the data to the database failed and has been rolled back; please try again.") :
		self.message = message
		super().__init__(self.message)


class KeyNotFound(Exception) :
	"""config item was not found or has not been added yet."""

	def __init__(self, key) :
		self.key = key
		self.message = f"`{key}` not found in config, please add it using /config"
		super().__init__(self.message)


class UserNotFound(Exception) :
	"""config item was not found or has not been added yet."""

	def __init__(self, key) :
		self.key = key
		self.message = f"`{key}` not found in config, please add it using /config"
		super().__init__(self.message)


class DatabaseTransactions(ABC) :

	@staticmethod
	@abstractmethod
	def commit(session) :
		try :
			session.commit()
		except pymysql.err.InternalError as e:
			logging.warning(e)
			session.rollback()
			raise CommitError()
		except SQLAlchemyError as e :
			logging.warning(e)
			session.rollback()
			raise CommitError()
		finally :
			session.close()

	@staticmethod
	@abstractmethod
	def ping_db() :
		try :
			session.connection()
			if session._is_clean():
				return "alive"
			session.execute(text("SELECT 1"))
			return "alive"
		except sqlalchemy.exc.PendingRollbackError :
			session.rollback()
			session.close()
			return "error"
		except sqlalchemy.exc.InvalidRequestError :
			return "alive"
		except Exception as e:
			logging.error(f"Database ping failed: {e}", exc_info=True)
			return "error"


class UserTransactions(ABC) :

	@staticmethod
	@abstractmethod
	def add_user_empty(userid: int, overwrite=False) :
		if UserTransactions.user_exists(userid) is True and overwrite is False :
			return False
		item = db.Users(uid=userid)
		session.merge(item)
		DatabaseTransactions.commit(session)
		return True

	@staticmethod
	@abstractmethod
	def add_user_full(userid, dob, guildname, override=False) :
		try :
			userdata: Users = UserTransactions.get_user(userid, deleted=override)
			if userdata is not None :
				UserTransactions.update_user_dob(userid, dob, guildname)
				return False
			item = db.Users(uid=userid, entry=datetime.now(tz=timezone.utc), date_of_birth=Encryption().encrypt(dob),
			                server=guildname)
			session.merge(item)
			DatabaseTransactions.commit(session)
			logging.info(f"User {userid} added to database with dob {dob} in {guildname}")
			return True
		except ValueError :
			return False

	@staticmethod
	@abstractmethod
	def update_user_dob(userid: int, dob: str, guildname: str, override=False) :
		userdata: Users = UserTransactions.get_user(userid, deleted=override)
		if userdata is None :
			UserTransactions.add_user_full(userid, dob, guildname)
			return False
		old_dob = userdata.date_of_birth
		userdata.date_of_birth = Encryption().encrypt(dob)
		userdata.entry = datetime.now(tz=timezone.utc)
		userdata.server = guildname
		userdata.deleted_at = None
		DatabaseTransactions.commit(session)
		logging.info(f"Dob updated for {userid} from {old_dob} to {dob} in {guildname}")
		if userdata.date_of_birth is None :
			return False
		return True

	@staticmethod
	@abstractmethod
	def update_user(uid: int, entry: datetime = None, date_of_birth: str = None, server: str = None, override=False) :
		user = UserTransactions.get_user(uid, deleted=override)
		data = {
			"entry"         : entry,
			"date_of_birth" : date_of_birth,
			"server"        : server
		}
		for field, value in data.items() :
			if field == 'date_of_birth' and value is not None :
				encrypted_value = Encryption().encrypt(value)
				setattr(user, field, encrypted_value)
			if value is not None :
				setattr(user, field, value)
		session.merge(user)
		DatabaseTransactions.commit(session)
		logging.info(f"Updated {uid} with:")
		logging.info(data)

	@staticmethod
	@abstractmethod
	def soft_delete(userid: int, guildname: str) :
		try :
			userdata: Users = UserTransactions.get_user(userid, deleted=True)
			if userdata is None :
				return False
			userdata.deleted_at = datetime.now()
			DatabaseTransactions.commit(session)
			logging.info(f"User {userid} soft-deleted by {guildname} ")
			return True
		except sqlalchemy.exc.IntegrityError :
			session.rollback()
			return False

	@staticmethod
	@abstractmethod
	def permanent_delete(userid: int, guildname: str) :
		try :
			userdata: Users = UserTransactions.get_user(userid, deleted=True)
			if userdata is None :
				return False
			session.delete(userdata)
			DatabaseTransactions.commit(session)
			logging.info(f"User {userid} permanently deleted by {guildname} ")
			return True
		except sqlalchemy.exc.IntegrityError :
			session.rollback()
			return False

	@staticmethod
	@abstractmethod
	def get_user(userid: int, deleted: bool = False) :
		if deleted :
			return session.scalar(Select(Users).where(Users.uid == userid))
		return session.scalar(Select(Users).where(and_(Users.uid == userid, Users.deleted_at.is_(None))))

	@staticmethod
	@abstractmethod
	def get_all_users(dob_only: bool = False) :
		if dob_only :
			return session.scalars(Select(Users).where(Users.date_of_birth != None)).all()
		userdata = session.scalars(Select(Users).outerjoin(IdVerification, Users.uid == IdVerification.uid)).all()
		session.close()
		return userdata

	@staticmethod
	@abstractmethod
	def update_entry_date(userid) :
		try :
			userdata = session.scalar(Select(Users).where(Users.uid == userid))
			userdata.entry = datetime.now()
			DatabaseTransactions.commit(session)
		except SQLAlchemyError :
			session.rollback()
			session.close()

	@staticmethod
	@abstractmethod
	def update() :
		raise NotImplementedError

	@staticmethod
	@abstractmethod
	def config_unique_remove(guildid: int, key: str) :
		if ConfigTransactions.key_exists_check(guildid, key) is False :
			return False
		exists = session.scalar(Select(db.Config).where(db.Config.guild == guildid, db.Config.key == key.upper()))
		session.delete(exists)
		DatabaseTransactions.commit(session)
		ConfigData().load_guild(guildid)
		return True

	@staticmethod
	@abstractmethod
	def user_exists(userid: int) :
		exists = session.scalar(
			Select(db.Users).where(db.Users.uid == userid))
		session.close()
		if exists is None :
			return False
		return True, exists

	# Warning related functions
	@staticmethod
	@abstractmethod
	def user_add_warning(userid: int, reason: str) :
		item = db.Warnings(uid=userid, reason=reason, type="WARN")
		session.add(item)
		DatabaseTransactions.commit(session)
		return True

	@staticmethod
	@abstractmethod
	def user_add_watchlist(userid: int, reason: str) :
		item = db.Warnings(uid=userid, reason=reason, type="WATCH")
		session.add(item)
		DatabaseTransactions.commit(session)
		return True

	@staticmethod
	@abstractmethod
	def user_get_warnings(userid: int, type) :
		warning_dict = {}
		warning_list = []
		warnings = session.scalars(
			Select(Warnings).where(Warnings.uid == userid, Warnings.type == type.upper()).order_by(Warnings.uid)).all()
		session.close()
		if len(warnings) == 0 or warnings is None :
			return False
		for warnings in warnings :
			warning_dict[warnings.id] = warnings.reason
			warning_list.append(warnings.id)
		return warning_list, warning_dict

	@staticmethod
	@abstractmethod
	def user_remove_warning(id: int) :
		warning = session.scalar(Select(Warnings).where(Warnings.id == id))
		session.delete(warning)
		DatabaseTransactions.commit(session)


# RULE: ALL db transactions have to go through this file. Keep to it dumbass
class ConfigTransactions(ABC) :

	@staticmethod
	@abstractmethod
	def config_unique_add(guildid: int, key: str, value, overwrite=False) :
		# This function should check if the item already exists, if so it will override it or throw an error.
		try:
			value = str(value)
			if ConfigTransactions.key_exists_check(guildid, key, overwrite) is True and overwrite is False :
				return False
			if ConfigTransactions.key_exists_check(guildid, key, overwrite) is True :
				entries = session.scalars(
					Select(db.Config).where(db.Config.guild == guildid, db.Config.key == key.upper())).all()
				for entry in entries :
					session.delete(entry)
			item = db.Config(guild=guildid, key=key.upper(), value=value)
			session.add(item)
			DatabaseTransactions.commit(session)
			ConfigData().load_guild(guildid)
			logging.info(f"Adding unique key with data: {guildid}, {key}, {value}, and overwrite {overwrite}")
			return True
		except sqlalchemy.exc.PendingRollbackError:
			logging.error("Pending rollback error occurred, rolling back session.")
			session.rollback()
			session.close()
			return False

	@staticmethod
	@abstractmethod
	def toggle_welcome(guildid: int, key: str, value) :
		# This function should check if the item already exists, if so it will override it or throw an error.
		value = str(value)
		guilddata = session.scalar(Select(Config).where(Config.guild == guildid, Config.key == key.upper()))
		if guilddata is None :
			ConfigTransactions.config_unique_add(guildid, key, value, overwrite=True)
			return
		guilddata.value = value
		DatabaseTransactions.commit(session)
		ConfigData().load_guild(guildid)
		return True

	@staticmethod
	@abstractmethod
	def config_unique_get(guildid: int, key: str) :
		if ConfigTransactions.key_exists_check(guildid, key) is False :
			return
		exists = session.scalar(Select(db.Config).where(db.Config.guild == guildid, db.Config.key == key.upper()))
		return exists

	@staticmethod
	@abstractmethod
	def config_key_add(guildid: int, key: str, value, overwrite) :
		value = str(value)
		if ConfigTransactions.key_multiple_exists_check(guildid, key, value) is True :
			return False
		item = db.Config(guild=guildid, key=key.upper(), value=value)
		session.add(item)
		DatabaseTransactions.commit(session)
		ConfigData().load_guild(guildid)
		return True

	@staticmethod
	@abstractmethod
	def key_multiple_exists_check(guildid: int, key: str, value) :
		exists = session.scalar(
			Select(db.Config).where(db.Config.guild == guildid, db.Config.key == key, db.Config.value == value))
		session.close()
		if exists is not None :
			return True
		return False

	@staticmethod
	@abstractmethod
	def config_key_remove(guildid: int, key: str, value) :
		if ConfigTransactions.key_multiple_exists_check(guildid, key, value) is False :
			return False
		exists = session.scalar(
			Select(db.Config).where(db.Config.guild == guildid, db.Config.key == key, db.Config.value == value))
		session.delete(exists)
		DatabaseTransactions.commit(session)
		ConfigData().load_guild(guildid)
		return None

	@staticmethod
	@abstractmethod
	def config_unique_remove(guild_id: int, key: str) :
		if ConfigTransactions.key_exists_check(guild_id, key) is False :
			return False
		exists = session.scalar(
			Select(db.Config).where(db.Config.guild == guild_id, db.Config.key == key))
		session.delete(exists)
		DatabaseTransactions.commit(session)
		return None

	@staticmethod
	@abstractmethod
	def key_exists_check(guildid: int, key: str, overwrite=False) :
		exists = session.scalar(
			Select(db.Config).where(db.Config.guild == guildid, db.Config.key == key.upper()))
		if exists is None :
			session.close()
			return False
		if overwrite is False :
			return True
		session.delete(exists)
		DatabaseTransactions.commit(session)
		return True

	@staticmethod
	@abstractmethod
	def toggle_add(guildid, key, value="DISABLED") :
		if ConfigTransactions.key_exists_check(guildid, key) is True :
			return
		toggle = Config(guild=guildid, key=key, value=value)
		session.merge(toggle)
		logging.info(f"Added toggle '{key}' with value '{value}' in {guildid}")
		DatabaseTransactions.commit(session)

	@staticmethod
	@abstractmethod
	def server_config_get(guildid) :
		return session.scalars(Select(db.Config).where(db.Config.guild == guildid)).all()


class VerificationTransactions(ABC) :

	@staticmethod
	@abstractmethod
	def id_exists(userid: int) -> bool :
		return session.query(IdVerification).where(IdVerification.uid == userid).count() > 0

	@staticmethod
	@abstractmethod
	def get_id_info(userid: int) -> IdVerification | None :
		userdata = session.scalar(Select(IdVerification).where(IdVerification.uid == userid))
		session.close()
		return userdata

	@staticmethod
	@abstractmethod
	def update_check(userid, reason: str = None, idcheck=True, server=None) :
		userdata = session.scalar(Select(IdVerification).where(IdVerification.uid == userid))
		if userdata is None :
			VerificationTransactions.add_idcheck(userid, reason, idcheck, server)
			return
		userdata.reason = reason
		userdata.idcheck = idcheck
		DatabaseTransactions.commit(session)

	@staticmethod
	@abstractmethod
	def add_idcheck(userid: int, reason: str = None, idcheck=True, server=None) :
		UserTransactions.add_user_empty(userid, True)
		idinfo = VerificationTransactions.get_id_info(userid)
		logging.info(idinfo)
		# if idinfo is not None :
		# 	return idinfo
		idcheck = IdVerification(uid=userid, reason=reason, idcheck=idcheck, server=server)
		session.add(idcheck)
		DatabaseTransactions.commit(session)
		return None

	@staticmethod
	@abstractmethod
	def set_idcheck_to_true(userid: int, reason, server=None) :
		userdata: IdVerification = session.scalar(Select(IdVerification).where(IdVerification.uid == userid))
		if userdata is None :
			VerificationTransactions.add_idcheck(userid, reason, idcheck=True, server=server)
			return
		userdata.idcheck = True
		userdata.reason = reason
		DatabaseTransactions.commit(session)

	@staticmethod
	@abstractmethod
	def set_idcheck_to_false(userid: int, server=None) :
		userdata: IdVerification = session.scalar(Select(IdVerification).where(IdVerification.uid == userid))
		if userdata is None :
			VerificationTransactions.add_idcheck(userid, idcheck=False, server=server)
			return
		userdata.idcheck = False
		userdata.reason = None
		DatabaseTransactions.commit(session)

	@staticmethod
	@abstractmethod
	def idverify_add(userid: int, dob: str, guildname, idcheck=True) :
		UserTransactions.add_user_empty(userid, True)
		idcheck = IdVerification(uid=userid, verifieddob=datetime.strptime(dob, "%m/%d/%Y"), idverified=idcheck)
		session.add(idcheck)
		DatabaseTransactions.commit(session)
		UserTransactions.update_user_dob(userid, dob, guildname=guildname)

	@staticmethod
	@abstractmethod
	def idverify_update(userid, dob: str, guildname, idverified=True, server=None) :

		userdata = session.scalar(Select(IdVerification).where(IdVerification.uid == userid))
		if userdata is None :
			VerificationTransactions.add_idcheck(userid, dob, idcheck=False, server=server)
			return
		userdata.verifieddob = datetime.strptime(dob, "%m/%d/%Y")
		userdata.idverified = idverified
		userdata.idcheck = False
		userdata.reason = "User ID Verified"
		DatabaseTransactions.commit(session)
		UserTransactions.update_user_dob(userid, dob, guildname=guildname)

	@staticmethod
	@abstractmethod
	def get_all() :
		return session.query(IdVerification).all()


class ConfigData(metaclass=singleton) :
	"""
	The goal of this class is to save the config to reduce database calls for the config; especially the roles.
	"""
	conf = {}

	def __init__(self) :
		pass

	def reload(self) :
		logging.info("reloading config")
		for guild_id in self.conf :
			self.load_guild(guild_id)
		logging.info(self.conf)

	def load_guild(self, guild_id: int) :
		config = ConfigTransactions.server_config_get(guild_id)
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
				ConfigTransactions.config_unique_remove(guild_id, x.key)
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
		try :
			return self.conf[guildid]
		except KeyError :
			raise ConfigNotFound

	def get_key_int(self, guildid: int, key: str) :
		try :
			return int(self.conf[guildid][key.upper()])
		except KeyError :
			raise KeyNotFound(key.upper())

	def get_key_int_or_zero(self, guildid: int, key: str) :
		return int(self.conf[guildid].get(key.upper(), 0))

	def get_key(self, guildid: int, key: str) :
		try :
			return self.conf[guildid][key.upper()]

		except KeyError :
			raise KeyNotFound(key.upper())

	def get_key_or_none(self, guildid: int, key: str) :
		return self.conf[guildid].get(key.upper(), None)

	def output_to_json(self) :
		"""This is for debugging only."""
		if os.path.isdir('debug') is False :
			os.mkdir('debug')
		with open('debug/config.json', 'w') as f :
			json.dump(self.conf, f, indent=4)


class AgeRoleTransactions() :
	def exists(self, role_id) :
		return session.scalar(Select(AgeRole).where(AgeRole.role_id == role_id))

	def get(self, guild_id, role_id) :
		return session.scalar(Select(AgeRole).where(AgeRole.guild_id == guild_id, AgeRole.role_id == role_id))

	def get_all(self, guild_id) :
		return session.scalars(Select(AgeRole).where(AgeRole.guild_id == guild_id)).all()

	def get_minimum_age(self, guild_id) :
		return session.scalars(Select(func.min(AgeRole.minimum_age)).where(AgeRole.guild_id == guild_id)).first()

	def add(self, guild_id, role_id, role_type, maximum_age=200, minimum_age=18, reload=True) :
		if self.exists(role_id) :
			return self.update(guild_id, role_id, role_type, maximum_age, minimum_age, reload=reload)
		role = db.AgeRole(guild_id=guild_id, role_id=role_id, type=role_type, maximum_age=maximum_age,
		                  minimum_age=minimum_age)
		session.merge(role)
		DatabaseTransactions.commit(session)
		if reload :
			ConfigData().load_guild(guild_id)
		return role

	def permanentdelete(self, guild_id, role_id) :
		role = session.scalar(Select(AgeRole).where(AgeRole.role_id == role_id))
		session.delete(role)
		DatabaseTransactions.commit(session)
		ConfigData().load_guild(guild_id)

	def update(self, guild_id: int, role_id: int, role_type: str = None, maximum_age: int = None,
	           minimum_age: int = None, reload=True) :
		role = session.scalar(Select(AgeRole).where(AgeRole.role_id == role_id))
		data = {
			"type"        : role_type.upper(),
			"maximum_age" : maximum_age,
			"minimum_age" : minimum_age
		}
		for field, value in data.items() :
			if value is not None :
				setattr(role, field, value)
		session.merge(role)
		DatabaseTransactions.commit(session)
		logging.info(f"Updated {role_id} with:")
		logging.info(data)
		if reload :
			ConfigData().load_guild(guild_id)

		return role


class TimersTransactions(ABC) :
	@staticmethod
	@abstractmethod
	def add_timer(guildid, userid, time_in_hours, roleid=None, reason=None) :
		"""Adds timer to the database"""
		entry = Timers(uid=userid, guild=guildid, removal=time_in_hours, role=roleid, reason=reason)
		session.add(entry)
		DatabaseTransactions.commit(session)

	@staticmethod
	@abstractmethod
	def get_timer_with_role(userid, guildid, roleid) :
		"""Gets the timer from the database with userid, guild and roleid"""
		timer = session.scalar(Select(Timers).where(Timers.uid == userid, Timers.guild == guildid, Timers.role == roleid))
		session.close()
		return timer

	@staticmethod
	@abstractmethod
	def remove_timer(id) :
		timer = session.scalar(Select(Timers).where(Timers.id == id))
		session.delete(timer)
		DatabaseTransactions.commit(session)


class ServerTransactions() :

	def add(self, guildid: int, active: bool = True, reload=True) :
		if self.get(guildid) is not None :
			self.update(guildid, active)
			ConfigTransactions.toggle_add(guildid, "AUTOKICK")
			ConfigTransactions.toggle_add(guildid, "AUTOMATIC")
			ConfigTransactions.toggle_add(guildid, "WELCOME", "ENABLED")
			ConfigTransactions.toggle_add(guildid, "UPDATEROLES")
			ConfigTransactions.config_unique_add(guildid, "COOLDOWN", 5)
			return
		g = db.Servers(guild=guildid, active=active)
		session.merge(g)
		DatabaseTransactions.commit(session)
		ConfigTransactions.toggle_add(guildid, "AUTOKICK")
		ConfigTransactions.toggle_add(guildid, "AUTOMATIC")
		ConfigTransactions.toggle_add(guildid, "WELCOME", "ENABLED")
		ConfigTransactions.toggle_add(guildid, "UPDATEROLES", "ENABLED")
		ConfigTransactions.config_unique_add(guildid, "COOLDOWN", 5)

		if reload :
			ConfigData().load_guild(guildid)

	def get_all(self, id_only=True) :
		if id_only is False :
			return session.query(Servers).all()
		return [sid[0] for sid in session.query(Servers.guild).all()]

	def get(self, guild_id: int) :
		return session.scalar(Select(Servers).where(Servers.guild == guild_id))

	def update(self, guild_id: int, active: bool = None, reload=True) :
		guild = self.get(guild_id)
		if not guild :
			return False
		updated_data = {
			"active" : active
		}
		for field, value in updated_data.items() :
			setattr(guild, field, value)
			logging.info(f"Updated {guild.guild} with:")
			logging.info(updated_data)
			DatabaseTransactions.commit(session)
			if reload :
				ConfigData().load_guild(guild_id)
		return
