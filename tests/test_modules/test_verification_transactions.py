import unittest

from classes.encryption import Encryption
from databases.Generators.uidgenerator import uidgenerator
from databases.current import create_bot_database, drop_bot_database
from databases.controllers.VerificationTransactions import VerificationTransactions
from databases.controllers.UserTransactions import UserTransactions
from databases.current import IdVerification


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

