import unittest

from databases.Generators.uidgenerator import uidgenerator
from databases.controllers.UserTransactions import UserTransactions
from databases.current import create_bot_database, drop_bot_database


class TestUserTransactions(unittest.TestCase) :
	def setUp(self) :
		create_bot_database()
		self.ut = UserTransactions()
		self.uid = uidgenerator().create()
		self.guild = "TestGuild"
		self.dob = "2000-01-01"

	def tearDown(self) :
		drop_bot_database()

	def test_add_user_empty(self) :
		result = self.ut.add_user_empty(self.uid)
		self.assertTrue(result)
		exists = self.ut.get_user(self.uid)
		self.assertIsNotNone(exists)
		# Adding again without overwrite should return False
		result2 = self.ut.add_user_empty(self.uid)
		self.assertFalse(result2)

		# # Adding again with overwrite should succeed
		# result3 = self.ut.add_user_empty(self.uid, overwrite=True)
		# self.assertTrue(result3)

	def test_add_user_full_and_get(self) :
		result = self.ut.add_user_full(self.uid, self.dob, self.guild)
		self.assertTrue(result)

		user = self.ut.get_user(self.uid)
		self.assertIsNotNone(user)
		self.assertEqual(user.uid, self.uid)
		self.assertEqual(user.server, self.guild)

	def test_update_user_dob(self) :
		self.ut.add_user_empty(self.uid)
		updated = self.ut.update_user_dob(self.uid, self.dob, self.guild)
		self.assertTrue(updated)

		user = self.ut.get_user(self.uid)
		self.assertIsNotNone(user)
		self.assertEqual(user.server, self.guild)

	def test_soft_delete(self) :
		self.ut.add_user_empty(self.uid)
		result = self.ut.soft_delete(self.uid, self.guild)
		self.assertTrue(result)

		user = self.ut.get_user(self.uid)
		self.assertIsNone(user)

		user_soft_deleted = self.ut.get_user(self.uid, deleted=True)
		self.assertIsNotNone(user_soft_deleted)
		self.assertIsNotNone(user_soft_deleted.deleted_at)

	def test_permanent_delete(self) :
		self.ut.add_user_empty(self.uid)
		self.ut.soft_delete(self.uid, self.guild)

		result = self.ut.permanent_delete(self.uid, self.guild)
		self.assertTrue(result)

		user = self.ut.get_user(self.uid, deleted=True)
		self.assertIsNone(user)

	def test_user_exists(self) :
		self.assertFalse(self.ut.user_exists(self.uid))
