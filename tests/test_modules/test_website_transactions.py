import unittest
from datetime import datetime, timedelta

from sqlalchemy import Select

from databases.Generators.guildgenerator import guildgenerator
from databases.Generators.uidgenerator import uidgenerator
from databases.current import WebsiteData, create_bot_database, drop_bot_database
from databases.transactions.UserTransactions import UserTransactions
from databases.transactions.WebsiteDataTransactions import WebsiteDataTransactions


class TestWebsiteDataTransactions(unittest.TestCase) :

	def setUp(self) -> None :
		create_bot_database()
		self.wt = WebsiteDataTransactions()
		self.ut = UserTransactions()
		self.uid = uidgenerator().create()
		self.gid = guildgenerator().create().guild
		self.ut.add_user_empty(self.uid)

	def tearDown(self) -> None :
		drop_bot_database()

	def _set_created_date(self, uuid: str, created_date: datetime) :
		with self.wt.createsession() as session :
			entry = session.scalar(Select(WebsiteData).where(WebsiteData.uuid == uuid))
			entry.created_date = created_date
			self.wt.commit(session)

	# create
	def test_create_returns_uuid_and_stores_record(self) :
		uuid = self.wt.create(self.uid, self.gid)

		self.assertIsInstance(uuid, str)
		entry = self.wt.read(uuid)
		self.assertIsNotNone(entry)
		self.assertEqual(entry.uid, self.uid)
		self.assertEqual(entry.gid, self.gid)
		self.assertIsNone(entry.verified)
		self.assertIsNotNone(entry.created_date)

	def test_create_generates_unique_uuids(self) :
		first = self.wt.create(self.uid, self.gid)
		second = self.wt.create(self.uid, self.gid)

		self.assertNotEqual(first, second)

	def test_create_adds_missing_user(self) :
		new_uid = uidgenerator().create()
		self.assertIsNone(self.ut.get_user(new_uid))

		uuid = self.wt.create(new_uid, self.gid)

		self.assertIsNotNone(self.ut.get_user(new_uid))
		self.assertEqual(self.wt.read(uuid).uid, new_uid)

	# read
	def test_read_nonexistent_returns_none(self) :
		self.assertIsNone(self.wt.read("does-not-exist"))

	def test_read_with_session(self) :
		uuid = self.wt.create(self.uid, self.gid)

		with self.wt.createsession() as session :
			entry = self.wt.read(uuid, session=session)
			self.assertIsNotNone(entry)
			self.assertEqual(entry.uuid, uuid)

	# set_verified
	def test_set_verified_sets_timestamp(self) :
		uuid = self.wt.create(self.uid, self.gid)

		self.assertTrue(self.wt.set_verified(uuid, self.uid))

		self.assertIsNotNone(self.wt.read(uuid).verified)

	def test_set_verified_nonexistent_returns_falsy(self) :
		self.assertFalse(self.wt.set_verified("does-not-exist", self.uid))

	def test_set_verified_rejects_mismatched_user(self) :
		uuid = self.wt.create(self.uid, self.gid)

		with self.assertRaises(ValueError) :
			self.wt.set_verified(uuid, self.uid + 1)

		self.assertIsNone(self.wt.read(uuid).verified)

	# owner_mismatch
	def test_owner_mismatch_false_for_owner(self) :
		uuid = self.wt.create(self.uid, self.gid)

		self.assertFalse(self.wt.owner_mismatch(uuid, self.uid, self.gid))

	def test_owner_mismatch_true_for_other_user(self) :
		uuid = self.wt.create(self.uid, self.gid)

		self.assertTrue(self.wt.owner_mismatch(uuid, self.uid + 1, self.gid))

	def test_owner_mismatch_true_for_other_guild(self) :
		uuid = self.wt.create(self.uid, self.gid)

		self.assertTrue(self.wt.owner_mismatch(uuid, self.uid, self.gid + 1))

	def test_owner_mismatch_false_for_unknown_guid(self) :
		self.assertFalse(self.wt.owner_mismatch("does-not-exist", self.uid, self.gid))

	# check
	def test_check_returns_uuid_for_pending_entry(self) :
		uuid = self.wt.create(self.uid, self.gid)

		self.assertEqual(self.wt.check(self.uid, self.gid, retrieve=True), uuid)

	def test_check_returns_true_without_retrieve(self) :
		self.wt.create(self.uid, self.gid)

		self.assertIs(self.wt.check(self.uid, self.gid, retrieve=False), True)

	def test_check_returns_false_when_no_entry(self) :
		self.assertFalse(self.wt.check(self.uid, self.gid))

	def test_check_ignores_other_guild(self) :
		other_gid = guildgenerator().create().guild
		self.wt.create(self.uid, other_gid)

		self.assertFalse(self.wt.check(self.uid, self.gid))

	def test_check_ignores_verified_entry(self) :
		uuid = self.wt.create(self.uid, self.gid)
		self.wt.set_verified(uuid, self.uid)

		self.assertFalse(self.wt.check(self.uid, self.gid))

	# clean_table
	def test_clean_table_removes_entries_older_than_90_days(self) :
		old_uuid = self.wt.create(self.uid, self.gid)
		recent_uuid = self.wt.create(self.uid, self.gid)
		self._set_created_date(old_uuid, datetime.now() - timedelta(days=91))
		self._set_created_date(recent_uuid, datetime.now() - timedelta(days=89))

		self.wt.clean_table()

		self.assertIsNone(self.wt.read(old_uuid))
		self.assertIsNotNone(self.wt.read(recent_uuid))

	# set_opened
	def _set_opened(self, uuid: str, opened: datetime) :
		with self.wt.createsession() as session :
			entry = session.scalar(Select(WebsiteData).where(WebsiteData.uuid == uuid))
			entry.opened = opened
			self.wt.commit(session)

	def test_set_opened_records_first_open_only(self) :
		uuid = self.wt.create(self.uid, self.gid)

		self.assertTrue(self.wt.set_opened(uuid, self.uid, self.gid))
		first = self.wt.read(uuid).opened
		self.assertIsNotNone(first)
		self.assertTrue(self.wt.set_opened(uuid, self.uid, self.gid))
		self.assertEqual(self.wt.read(uuid).opened, first)

	def test_set_opened_rejects_mismatched_ids(self) :
		uuid = self.wt.create(self.uid, self.gid)
		other_gid = guildgenerator().create().guild

		self.assertFalse(self.wt.set_opened(uuid, self.uid, other_gid))
		self.assertFalse(self.wt.set_opened(uuid, self.uid + 1, self.gid))
		self.assertFalse(self.wt.set_opened("does-not-exist", self.uid, self.gid))
		self.assertIsNone(self.wt.read(uuid).opened)

	# get_abandoned / set_reminded
	def _abandoned_uuids(self) :
		return {entry.uuid for entry in self.wt.get_abandoned(timedelta(days=7))}

	def test_get_abandoned_returns_opened_unfinished_links(self) :
		opened = self.wt.create(self.uid, self.gid)
		self.wt.set_opened(opened, self.uid, self.gid)
		never_opened = self.wt.create(self.uid, self.gid)

		result = self._abandoned_uuids()

		self.assertIn(opened, result)
		self.assertNotIn(never_opened, result)

	def test_get_abandoned_skips_verified_and_reminded(self) :
		verified = self.wt.create(self.uid, self.gid)
		self.wt.set_opened(verified, self.uid, self.gid)
		self.wt.set_verified(verified, self.uid)
		reminded = self.wt.create(self.uid, self.gid)
		self.wt.set_opened(reminded, self.uid, self.gid)

		self.assertTrue(self.wt.set_reminded(reminded))
		result = self._abandoned_uuids()

		self.assertNotIn(verified, result)
		self.assertNotIn(reminded, result)

	def test_get_abandoned_ignores_links_older_than_max_age(self) :
		old = self.wt.create(self.uid, self.gid)
		self._set_opened(old, datetime.now() - timedelta(days=8))

		self.assertNotIn(old, self._abandoned_uuids())


if __name__ == '__main__' :
	unittest.main()
