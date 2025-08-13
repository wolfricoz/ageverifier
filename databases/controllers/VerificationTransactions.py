import logging
from datetime import datetime

from sqlalchemy import Select

from classes.encryption import Encryption
from databases.controllers.DatabaseTransactions import DatabaseTransactions
from databases.controllers.UserTransactions import UserTransactions
from databases.current import IdVerification


class VerificationTransactions(DatabaseTransactions) :

	def id_exists(self, userid: int) -> bool :
		with self.createsession() as session :
			return session.query(IdVerification).where(IdVerification.uid == userid).count() > 0

	def get_id_info(self, userid: int, session = None) -> IdVerification | None :
		if session:
			return session.scalar(Select(IdVerification).where(IdVerification.uid == userid))
		with self.createsession() as session :
			return session.scalar(Select(IdVerification).where(IdVerification.uid == userid))


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
			idcheck = IdVerification(uid=userid, verifieddob=Encryption().encrypt(dob), idverified=idcheck)
			session.add(idcheck)
			self.commit(session)
			UserTransactions().update_user_dob(userid, dob, guildname=guildname)

	def idverify_update(self, userid, dob: str, guildname, idverified=True, server=None) :
		with self.createsession() as session :

			userdata = session.scalar(Select(IdVerification).where(IdVerification.uid == userid))
			if userdata is None :
				verification = IdVerification(uid=userid, reason="User ID Verified", idcheck=False, idverified=idverified, verifieddob=Encryption().encrypt(dob), server=server)
				session.add(verification)
				self.commit(session)
				UserTransactions().update_user_dob(userid, dob, guildname=guildname, override=True)
				return
			userdata.verifieddob = Encryption().encrypt(dob)
			userdata.idverified = idverified
			userdata.idcheck = False
			userdata.reason = "User ID Verified"
			self.commit(session)
			UserTransactions().update_user_dob(userid, dob, guildname=guildname, override=True)

	def update_verification(self, uid: int, reason: str = None, idcheck: bool = None,
	                        idverified: bool = None, verifieddob: str = None, server: str = None) :
		with self.createsession() as session :
			verification = self.get_id_info(uid, session=session)  # Assumes you have a method to retrieve the record

			data = {
				"reason"      : reason,
				"idcheck"     : idcheck,
				"idverified"  : idverified,
				"verifieddob" : verifieddob,
				"server"      : server
			}

			for field, value in data.items() :
				if field == 'verifieddob' and value is not None :
					encrypted_value = Encryption().encrypt(value)
					setattr(verification, field, encrypted_value)
				elif value is not None :
					setattr(verification, field, value)

			session.merge(verification)
			self.commit(session)
			logging.info(f"Updated verification for {uid} with:")
			logging.info(data)

	def get_all(self, ) :
		with self.createsession() as session :
			return session.query(IdVerification).all()

	# def migrate(self):
	# 	with self.createsession() as session :
	# 		records = self.get_all()
	# 		for record in records :
	# 			if record.idverified is False or record.verifieddob is None:
	# 				continue
	# 			try:
	# 				dt = record.verifieddob
	# 				if isinstance(record.verifieddob, str) :
	# 					dt = datetime.strptime(record.verifieddob, "%Y-%m-%d %H:%M:%S")
	# 				formatted_date = dt.strftime("%m/%d/%Y")
	# 			except Exception as e:
	# 				logging.warning(f"failed to convert verifieddob to datetime for {record.uid} with {record.verifieddob}: {e}")
	# 				continue
	# 			self.update_verification(record.uid, record.reason, record.idcheck, record.idverified, formatted_date, record.server)

