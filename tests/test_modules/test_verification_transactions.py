import unittest
from datetime import datetime, timedelta

from sqlalchemy import Update

from classes.encryption import Encryption
from databases.Generators.uidgenerator import uidgenerator
from databases.transactions.UserTransactions import UserTransactions
from databases.transactions.VerificationTransactions import VerificationTransactions
from databases.current import IdVerification, create_bot_database, drop_bot_database


class TestVerificationTransactions(unittest.TestCase) :

	def setUp(self) -> None :
		create_bot_database()
		self.vt = VerificationTransactions()
		self.ut = UserTransactions()
		self.uid = uidgenerator().create()

	def tearDown(self) -> None :
		drop_bot_database()

	def test_add_and_get_id_info(self) :
		self.vt.add_idcheck(self.uid, reason="Testing", idcheck=True, server="TestServer")
		info = self.vt.get_id_info(self.uid)
		self.assertIsNotNone(info)
		self.assertEqual(info.uid, self.uid)
		self.assertEqual(info.reason, "Testing")
		self.assertTrue(info.idcheck)

	def test_update_check_existing(self) :
		self.vt.add_idcheck(self.uid, reason="Initial", idcheck=False)
		self.vt.update_check(self.uid, reason="Updated", idcheck=True)
		info = self.vt.get_id_info(self.uid)
		self.assertEqual(info.reason, "Updated")
		self.assertTrue(info.idcheck)

	def test_update_check_non_existing(self) :
		self.vt.update_check(self.uid, reason="Inserted by update_check", idcheck=True)
		info = self.vt.get_id_info(self.uid)
		self.assertIsNotNone(info)
		self.assertEqual(info.reason, "Inserted by update_check")
		self.assertTrue(info.idcheck)

	def test_set_idcheck_to_true_and_false(self) :
		self.vt.set_idcheck_to_true(self.uid, reason="InitialTrue")
		info = self.vt.get_id_info(self.uid)
		self.assertTrue(info.idcheck)
		self.assertEqual(info.reason, "InitialTrue")

		self.vt.set_idcheck_to_false(self.uid)
		info = self.vt.get_id_info(self.uid)
		self.assertFalse(info.idcheck)
		self.assertIsNone(info.reason)

	def test_id_exists(self) :
		self.assertFalse(self.vt.id_exists(self.uid))
		self.vt.add_idcheck(self.uid)
		self.assertTrue(self.vt.id_exists(self.uid))

	def test_idverify_add(self) :
		self.vt.idverify_add(self.uid, "01/01/2000", guildname="GuildName")
		info = self.vt.get_id_info(self.uid)
		self.assertIsNotNone(info)
		self.assertEqual(Encryption().decrypt(info.verifieddob), "01/01/2000")
		self.assertTrue(info.idverified)

	def test_idverify_update(self) :
		self.vt.idverify_add(self.uid, "01/01/1990", guildname="GuildName")
		self.vt.idverify_update(self.uid, "02/02/1992", guildname="GuildName")
		info = self.vt.get_id_info(self.uid)
		self.assertEqual(Encryption().decrypt(info.verifieddob), "02/02/1992")
		self.assertTrue(info.idverified)
		self.assertFalse(info.idcheck)
		self.assertEqual(info.reason, "User ID Verified")

	def test_get_all(self) :
		self.vt.add_idcheck(self.uid, reason="Test1")
		self.vt.add_idcheck(uidgenerator().create(), reason="Test2")
		all_entries = self.vt.get_all()
		self.assertEqual(len(all_entries), 2)


	# get_expired_idmessages / remove_idmessage
	def _set_idmessage(self, uid: int, message_id: int, created) :
		self.vt.update_verification(uid, idmessage=message_id)
		with self.vt.createsession() as session :
			session.execute(Update(IdVerification).where(IdVerification.uid == uid).values(idmessagecreated=created))
			session.commit()

	def test_get_expired_idmessages_returns_old_and_undated_messages_only(self) :
		old, recent, undated = self.uid, uidgenerator().create(), uidgenerator().create()
		self._set_idmessage(old, 1, datetime.now() - timedelta(days=8))
		self._set_idmessage(recent, 2, datetime.now() - timedelta(days=1))
		self._set_idmessage(undated, 3, None)

		expired = {record.uid for record in self.vt.get_expired_idmessages(timedelta(days=7))}

		self.assertEqual(expired, {old, undated})

	def test_removed_idmessages_no_longer_expire(self) :
		self._set_idmessage(self.uid, 1, datetime.now() - timedelta(days=8))
		self.vt.remove_idmessage(self.uid)

		self.assertEqual(self.vt.get_expired_idmessages(timedelta(days=7)), [])

	def test_remove_idmessage_without_a_record_does_nothing(self) :
		self.vt.remove_idmessage(self.uid)
		self.assertIsNone(self.vt.get_id_info(self.uid))
