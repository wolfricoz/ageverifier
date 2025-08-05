import datetime
import logging

from sqlalchemy import Select

from databases.controllers.DatabaseTransactions import DatabaseTransactions
from databases.controllers.UserTransactions import UserTransactions
from databases.current import IdVerification
from datetime import datetime


class VerificationTransactions(DatabaseTransactions) :

	def id_exists(self, userid: int) -> bool :
		with self.createsession() as session :
			return session.query(IdVerification).where(IdVerification.uid == userid).count() > 0

	def get_id_info(self, userid: int) -> IdVerification | None :
		with self.createsession() as session :
			userdata = session.scalar(Select(IdVerification).where(IdVerification.uid == userid))
			session.close()
			return userdata

	def update_check(self, userid, reason: str = None, idcheck=True, server=None) :
		with self.createsession() as session :
			userdata = session.scalar(Select(IdVerification).where(IdVerification.uid == userid))
			if userdata is None :
				VerificationTransactions().add_idcheck(userid, reason, idcheck, server)
				return
			userdata.reason = reason
			userdata.idcheck = idcheck
			self.commit(session)

	def add_idcheck(self, userid: int, reason: str = None, idcheck=True, server=None) :
		with self.createsession() as session :
			UserTransactions().add_user_empty(userid, True)
			idinfo = VerificationTransactions().get_id_info(userid)
			logging.info(idinfo)
			# if idinfo is not None :
			# 	return idinfo
			idcheck = IdVerification(uid=userid, reason=reason, idcheck=idcheck, server=server)
			session.add(idcheck)
			self.commit(session)
			return None

	def set_idcheck_to_true(self, userid: int, reason, server=None) :
		with self.createsession() as session :
			userdata: IdVerification = session.scalar(Select(IdVerification).where(IdVerification.uid == userid))
			if userdata is None :
				VerificationTransactions().add_idcheck(userid, reason, idcheck=True, server=server)
				return
			userdata.idcheck = True
			userdata.reason = reason
			self.commit(session)

	def set_idcheck_to_false(self, userid: int, server=None) :
		with self.createsession() as session :
			userdata: IdVerification = session.scalar(Select(IdVerification).where(IdVerification.uid == userid))
			if userdata is None :
				VerificationTransactions().add_idcheck(userid, idcheck=False, server=server)
				return
			userdata.idcheck = False
			userdata.reason = None
			self.commit(session)

	def idverify_add(self, userid: int, dob: str, guildname, idcheck=True) :
		with self.createsession() as session :
			UserTransactions().add_user_empty(userid, True)
			idcheck = IdVerification(uid=userid, verifieddob=datetime.strptime(dob, "%m/%d/%Y"), idverified=idcheck)
			session.add(idcheck)
			self.commit(session)
			UserTransactions().update_user_dob(userid, dob, guildname=guildname)

	def idverify_update(self, userid, dob: str, guildname, idverified=True, server=None) :
		with self.createsession() as session :

			userdata = session.scalar(Select(IdVerification).where(IdVerification.uid == userid))
			if userdata is None :
				VerificationTransactions().add_idcheck(userid, dob, idcheck=False, server=server)
				return
			userdata.verifieddob = datetime.strptime(dob, "%m/%d/%Y")
			userdata.idverified = idverified
			userdata.idcheck = False
			userdata.reason = "User ID Verified"
			self.commit(session)
			UserTransactions().update_user_dob(userid, dob, guildname=guildname)

	def get_all(self, ) :
		with self.createsession() as session :
			return session.query(IdVerification).all()
