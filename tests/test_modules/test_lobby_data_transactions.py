import unittest
from datetime import datetime

from classes.encryption import Encryption
from databases.controllers.ButtonTransactions import LobbyDataTransactions
from databases.controllers.UserTransactions import UserTransactions
from databases.current import create_bot_database, drop_bot_database


# Assuming these are defined elsewhere in your project
# from databases.current import create_bot_database, drop_bot_database
# from databases.controllers.LobbyDataTransactions import LobbyDataTransactions
# from databases.models.LobbyData import LobbyData

class TestLobbyDataTransactions(unittest.TestCase) :
	"""
	Test suite for the LobbyDataTransactions controller.
	This test suite assumes the existence of `create_bot_database()` and
	`drop_bot_database()` functions that manage an in-memory or temporary
	database for testing, ensuring each test runs in an isolated environment.
	"""

	def setUp(self) :
		"""
		Set up a clean database for each test and define test data.
		"""
		# This function should create a temporary database for the test
		create_bot_database()
		USERID = 123455656
		user = UserTransactions().add_user_empty(USERID)
		# Define some unique data for testing
		self.user = USERID
		self.message_id = 1234567890
		self.verified_dob = "1995-10-25"
		self.age = 28
		self.non_existent_message_id = 9999999999
		self.controller = LobbyDataTransactions()

	def tearDown(self) :
		"""
		Drop the database after each test to ensure isolation.
		"""
		# This function should drop the temporary database
		drop_bot_database()

	def test_create_record(self) :
		"""
		Tests creating a new LobbyData record.
		"""
		# WHEN creating a new record

		new_entry = self.controller.create(
			uuid=self.message_id,
			user_id= self.user,
			dob=self.verified_dob,
			age=self.age
		)

		# THEN the returned object is correct
		self.assertIsNotNone(new_entry)
		self.assertEqual(new_entry.uuid, self.message_id)
		self.assertEqual(Encryption().decrypt(new_entry.dob), self.verified_dob)
		self.assertEqual(new_entry.age, self.age)

	def test_read_record_found(self) :
		"""
		Tests retrieving an existing LobbyData record.
		"""
		# GIVEN a record has been created
		self.controller.create(
			uuid=self.message_id,
			user_id=self.user,
			dob=self.verified_dob,
			age=self.age
		)

		# WHEN reading the record by its message_id
		found_entry = self.controller.read(self.message_id)

		# THEN the correct record is returned
		self.assertIsNotNone(found_entry)
		self.assertEqual(found_entry.uuid, str(self.message_id))
		self.assertEqual(Encryption().decrypt(found_entry.dob), self.verified_dob)

	def test_read_record_not_found(self) :
		"""
		Tests that reading a non-existent record returns None.
		"""
		# WHEN reading with a non-existent message_id
		found_entry = self.controller.read(self.non_existent_message_id)

		# THEN the result is None
		self.assertIsNone(found_entry)

	def test_delete_record_success(self) :
		"""
		Tests successfully deleting an existing record.
		"""
		# GIVEN a record exists
		self.controller.create(
			uuid=self.message_id,
			user_id=self.user,
			dob=self.verified_dob,
			age=self.age
		)
		self.assertIsNotNone(self.controller.read(self.message_id))

		# WHEN deleting the record
		is_deleted = self.controller.delete(self.message_id)

		# THEN the method returns True and the record is no longer in the database
		self.assertTrue(is_deleted)
		self.assertIsNone(self.controller.read(self.message_id))

	def test_delete_record_not_found(self) :
		"""
		Tests that attempting to delete a non-existent record returns False.
		"""
		# WHEN deleting a non-existent record
		is_deleted = self.controller.delete(self.non_existent_message_id)

		# THEN the method returns False
		self.assertFalse(is_deleted)
