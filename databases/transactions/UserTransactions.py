import datetime
import logging
from datetime import datetime, timezone

import sqlalchemy.exc
from sqlalchemy import Select, and_
from sqlalchemy.exc import SQLAlchemyError

from classes.encryption import Encryption
from databases import current as db
from databases.transactions.ConfigData import ConfigData
from databases.transactions.ConfigTransactions import ConfigTransactions
from databases.transactions.DatabaseTransactions import DatabaseTransactions
from databases.current import IdVerification, Users, Warnings


class UserTransactions(DatabaseTransactions) :


	def add_user_empty(self, userid: int, overwrite=False) :
		with self.createsession() as session :
			userdata: Users = self.get_user(userid, deleted=True)

			if userdata:
				#to fix error, overwrite was removed.
				return False
			item = db.Users(uid=userid)
			if overwrite :
				session.merge(item)
			else:
				session.add(item)
			self.commit(session)
			return True


	def add_user_full(self, userid, dob, guildname, override=False) :
		with self.createsession() as session :
			try :
				userdata: Users = self.get_user(userid, deleted=override)
				if userdata is not None :
					self.update_user_dob(userid, dob, guildname)
					return False
				# noinspection PyTypeChecker
				item = db.Users(uid=userid, entry=datetime.now(tz=timezone.utc), date_of_birth=Encryption().encrypt(dob),
				                server=guildname)
				session.add(item)
				self.commit(session)
				logging.info(f"User {userid} added to database with dob {dob} in {guildname}")
				return True
			except ValueError :
				return False


	def update_user_dob(self, userid: int, dob: str, guildname: str, override=False) :
		with self.createsession() as session :
			userdata: Users = self.get_user(userid, deleted=override, session=session)
			if userdata is None :
				self.add_user_full(userid, dob, guildname)
				return False
			old_dob = userdata.date_of_birth
			# noinspection PyTypeChecker
			userdata.date_of_birth = Encryption().encrypt(dob)
			userdata.entry = datetime.now(tz=timezone.utc)
			userdata.server = guildname
			userdata.deleted_at = None
			self.commit(session)
			logging.info(f"Dob updated for {userid} from {old_dob} to {dob} in {guildname}")
			if userdata.date_of_birth is None :
				return False
			return True


	def update_user(self, uid: int, entry: datetime = None, date_of_birth: str = None, server: str = None, override=False) :
		with self.createsession() as session :
			user = self.get_user(uid, deleted=override)
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
			self.commit(session)
			logging.info(f"Updated {uid} with:")
			logging.info(data)


	def soft_delete(self, userid: int, guildname: str) :
		with self.createsession() as session :

			try :
				userdata: Users = self.get_user(userid, deleted=True, session=session)
				if userdata is None :
					return False
				userdata.deleted_at = datetime.now()
				self.commit(session)
				logging.info(f"User {userid} soft-deleted by {guildname} ")
				return True
			except sqlalchemy.exc.IntegrityError :
				session.rollback()
				return False


	def permanent_delete(self, userid: int, guildname: str) :
		with self.createsession() as session :

			try :
				userdata: Users = self.get_user(userid, deleted=True)
				if userdata is None :
					return False
				session.delete(userdata)
				self.commit(session)
				logging.info(f"User {userid} permanently deleted by {guildname} ")
				return True
			except sqlalchemy.exc.IntegrityError :
				session.rollback()
				return False


	def get_user(self, userid: int, deleted: bool = False, session = None) :
		if session:
			if deleted :
				return session.scalar(Select(Users).where(Users.uid == userid))
			return session.scalar(Select(Users).where(and_(Users.uid == userid, Users.deleted_at.is_(None))))
		with self.createsession() as session :
			if deleted :
				return session.scalar(Select(Users).where(Users.uid == userid))
			return session.scalar(Select(Users).where(and_(Users.uid == userid, Users.deleted_at.is_(None))))


	def get_all_users(self, dob_only: bool = False) :
		with self.createsession() as session :
			if dob_only :
				return session.scalars(Select(Users).where(Users.date_of_birth != None)).all()
			userdata = session.scalars(Select(Users).outerjoin(IdVerification, Users.uid == IdVerification.uid)).all()
			session.close()
			return userdata


	def update_entry_date(self, userid) :
		with self.createsession() as session :

			try :
				userdata = session.scalar(Select(Users).where(Users.uid == userid))
				userdata.entry = datetime.now()
				self.commit(session)
			except SQLAlchemyError :
				session.rollback()
				session.close()


	def update(self, ) :
		raise NotImplementedError


	def config_unique_remove(self, guildid: int, key: str) :
		with self.createsession() as session :

			if ConfigTransactions().key_exists_check(guildid, key) is False :
				return False
			exists = session.scalar(Select(db.Config).where(db.Config.guild == guildid, db.Config.key == key.upper()))
			session.delete(exists)
			self.commit(session)
			ConfigData().load_guild(guildid)
			return True


	def user_exists(self, userid: int) :
		with self.createsession() as session :
			exists = session.scalar(
				Select(db.Users).where(db.Users.uid == int(userid)))
			session.close()
			if exists is None :
				return False
			return True, exists

	# Warning related functions

	def user_add_warning(self, userid: int, reason: str) :
		with self.createsession() as session :

			item = db.Warnings(uid=userid, reason=reason, type="WARN")
			session.add(item)
			self.commit(session)
			return True


	def user_add_watchlist(self, userid: int, reason: str) :
		with self.createsession() as session :

			item = db.Warnings(uid=userid, reason=reason, type="WATCH")
			session.add(item)
			self.commit(session)
			return True


	def user_get_warnings(self, userid: int, warning_type: str) :
		with self.createsession() as session :

			warning_dict = {}
			warning_list = []
			warnings = session.scalars(
				Select(Warnings).where(Warnings.uid == userid, Warnings.type == warning_type.upper()).order_by(Warnings.uid)).all()
			session.close()
			if len(warnings) == 0 or warnings is None :
				return False
			for warnings in warnings :
				warning_dict[warnings.id] = warnings.reason
				warning_list.append(warnings.id)
			return warning_list, warning_dict


	def user_remove_warning(self,warning_id: int) :
		with self.createsession() as session :

			warning = session.scalar(Select(Warnings).where(Warnings.id == warning_id))
			session.delete(warning)
			self.commit(session)
