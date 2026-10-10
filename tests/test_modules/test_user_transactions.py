import unittest
from datetime import datetime, timedelta, timezone

from databases.Generators.uidgenerator import uidgenerator
from databases.current import create_bot_database, drop_bot_database
from databases.transactions.UserTransactions import UserTransactions
from classes.iphash import hash_fingerprint, hash_ip
from resources.data.config_variables import GDPR_REMOVAL_GRACE_DAYS, IP_RETENTION_DAYS
from sqlalchemy import Update
from databases.current import Users


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

	def test_get_pending_removal(self) :
		self.ut.add_user_empty(self.uid)
		self.assertIsNone(self.ut.get_pending_removal(self.uid))

		self.ut.soft_delete(self.uid, self.guild)
		removal_date = self.ut.get_pending_removal(self.uid)
		self.assertIsNotNone(removal_date)

		user = self.ut.get_user(self.uid, deleted=True)
		self.assertEqual(removal_date, user.deleted_at + timedelta(days=GDPR_REMOVAL_GRACE_DAYS))

		# Re-submitting a date of birth cancels the removal, so nothing should be pending afterwards.
		self.ut.update_user_dob(self.uid, self.dob, self.guild, override=True)
		self.assertIsNone(self.ut.get_pending_removal(self.uid))

	def test_get_pending_removal_unknown_user(self) :
		self.assertIsNone(self.ut.get_pending_removal(self.uid))

	def test_permanent_delete(self) :
		self.ut.add_user_empty(self.uid)
		self.ut.soft_delete(self.uid, self.guild)

		result = self.ut.permanent_delete(self.uid, self.guild)
		self.assertTrue(result)

		user = self.ut.get_user(self.uid, deleted=True)
		self.assertIsNone(user)

	def test_user_exists(self) :
		self.assertFalse(self.ut.user_exists(self.uid))

	def test_fingerprint_is_stored_peppered_and_matches_other_users(self) :
		fingerprint = "ab" * 32
		other = uidgenerator().create()
		self.ut.add_user_empty(self.uid)
		self.ut.add_user_empty(other)
		self.ut.update_user(self.uid, device_fingerprint=fingerprint)
		self.ut.update_user(other, device_fingerprint=fingerprint)

		user = self.ut.get_user(self.uid)
		self.assertNotEqual(user.device_fingerprint, fingerprint)
		self.assertEqual(user.device_fingerprint, hash_fingerprint(fingerprint))
		self.assertIsNotNone(user.fingerprint_recorded_at)

		matches = self.ut.check_duplicate_fingerprints(hash_fingerprint(fingerprint), exclude_uid=self.uid)
		self.assertEqual([match.uid for match in matches], [other])

	def test_users_pending_gdpr_removal_are_not_matched_as_alts(self) :
		fingerprint = "cd" * 32
		address = "203.0.113.7"
		pending = uidgenerator().create()
		for uid in (self.uid, pending) :
			self.ut.add_user_empty(uid)
			self.ut.update_user(uid, ip_address=address, device_fingerprint=fingerprint)
		self.ut.soft_delete(pending, self.guild)

		ip_hash = hash_ip(address)["ip_hash"]
		self.assertEqual(self.ut.check_duplicate_ips(ip_hash, exclude_uid=self.uid), [])
		self.assertEqual(self.ut.check_duplicate_fingerprints(hash_fingerprint(fingerprint), exclude_uid=self.uid), [])

	def test_an_empty_fingerprint_matches_nobody(self) :
		self.ut.add_user_empty(self.uid)
		self.assertEqual(self.ut.check_duplicate_fingerprints(None), [])

	def test_a_malformed_fingerprint_is_not_stored(self) :
		self.ut.add_user_empty(self.uid)
		self.ut.update_user(self.uid, device_fingerprint="not-a-hash")
		self.assertIsNone(self.ut.get_user(self.uid).device_fingerprint)

	def test_expired_fingerprints_are_cleared(self) :
		self.ut.add_user_empty(self.uid)
		self.ut.update_user(self.uid, device_fingerprint="ab" * 32)
		with self.ut.createsession() as session :
			session.execute(Update(Users).where(Users.uid == self.uid).values(
				fingerprint_recorded_at=datetime.now(tz=timezone.utc) - timedelta(days=IP_RETENTION_DAYS + 1)))
			session.commit()

		self.ut.clear_expired_ips()

		user = self.ut.get_user(self.uid)
		self.assertIsNone(user.device_fingerprint)
		self.assertIsNone(user.fingerprint_recorded_at)
