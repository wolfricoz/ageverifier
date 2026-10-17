import asyncio
import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from classes.support import quickleaves
from classes.support.logreader import read_records

GUILD = 612345678901234567
OTHER = 798765432109876543


def _log_lines(now: datetime) -> list[str] :
	stamp = lambda delta : (now - delta).strftime("%Y-%m-%d %H:%M:%S")
	return [
		f"{stamp(timedelta(days=30))},001:root:INFO: Test({GUILD}): someone(1) issued appcommand: `old` with arguments: {{}}\n",
		f"{stamp(timedelta(hours=2))},001:root:INFO: Test({GUILD}): someone(1) issued appcommand: `setup` with arguments: {{}}\n",
		f"{stamp(timedelta(hours=1))},002:root:INFO: Test({GUILD}): someone(1) issued appcommand: `setup` with arguments: {{}}\n",
		f"{stamp(timedelta(hours=1))},003:root:INFO: Other({OTHER}): x(2) issued appcommand: `help` with arguments: {{}}\n",
		f"{stamp(timedelta(minutes=30))},004:root:WARNING: \n",
		f"Test {GUILD} config with arguments {{}}: Traceback (most recent call last):\n",
		"  KeyError: 'age_log'\n",
		f"{stamp(timedelta(minutes=20))},005:root:INFO: 1{GUILD}9 is a different number\n",
		f"{stamp(timedelta(minutes=10))},006:root:INFO: Test({GUILD}): someone(1) issued command: ping\n",
	]


class TestQuickLeaves(unittest.TestCase) :

	def setUp(self) :
		self.folder = tempfile.TemporaryDirectory()
		self.now = datetime.now()
		self.log = os.path.join(self.folder.name, "log.txt")
		with open(self.log, "w", encoding="utf-8") as file :
			file.writelines(_log_lines(self.now))

	def tearDown(self) :
		self.folder.cleanup()

	def _records(self, since: datetime) :
		return quickleaves.server_records(GUILD, read_records(since, [self.log]))

	def test_records_for_the_server_since_it_joined(self) :
		records = self._records(self.now - timedelta(days=1))

		self.assertEqual(len(records), 4)
		# A traceback is kept whole even though the guild id is on its second line.
		self.assertIn("KeyError: 'age_log'", records[2].text)
		self.assertTrue(all(str(OTHER) not in record.text for record in records))

	def test_command_counts(self) :
		counts = quickleaves.command_counts(self._records(self.now - timedelta(days=1)))

		self.assertEqual(counts, {"setup" : 2, "ping" : 1})

	def test_build_file(self) :
		joined = datetime(2026, 9, 27, 10, tzinfo=timezone.utc)
		text = quickleaves.build_file(GUILD, "Test", "owner(5)", 40, joined, joined + timedelta(hours=26, minutes=5),
		                              self._records(self.now - timedelta(days=1)))

		self.assertIn(f"Server: Test ({GUILD})", text)
		self.assertIn("Time in server: 1d 2h 5m", text)
		self.assertIn("Commands: 3", text)
		self.assertIn("  setup: 2", text)
		self.assertIn("KeyError: 'age_log'", text)

	def _guild(self, joined_at) :
		return SimpleNamespace(id=GUILD, name="Test", owner="owner", owner_id=5, member_count=40,
		                       me=SimpleNamespace(joined_at=joined_at))

	def _capture(self, guild, folder) :
		records = lambda since : read_records(since, [self.log])
		with patch.object(quickleaves, "QUICK_LEAVE_DIR", folder), \
				patch.object(quickleaves, "read_records", side_effect=records), \
				patch.object(quickleaves.asyncio, "sleep", new=AsyncMock()) :
			return asyncio.run(quickleaves.capture(guild))

	def test_capture_saves_a_quick_leave(self) :
		folder = os.path.join(self.folder.name, "quick")
		path = self._capture(self._guild(datetime.now(tz=timezone.utc) - timedelta(days=1)), folder)

		self.assertIsNotNone(path)
		saved = quickleaves.saved_since(self.now - timedelta(minutes=5), folder)
		self.assertEqual(len(saved), 1)
		self.assertEqual(saved[0].commands, 3)
		self.assertEqual(saved[0].name, f"Test ({GUILD})")

	def test_capture_skips_a_server_that_stayed(self) :
		folder = os.path.join(self.folder.name, "quick")
		guild = self._guild(datetime.now(tz=timezone.utc) - timedelta(days=quickleaves.QUICK_LEAVE_DAYS + 1))

		self.assertIsNone(self._capture(guild, folder))
		self.assertFalse(os.path.exists(folder))

	def test_capture_skips_a_server_without_commands(self) :
		folder = os.path.join(self.folder.name, "quick")
		# Joined after every command in the log was issued.
		guild = self._guild(datetime.now(tz=timezone.utc) - timedelta(minutes=5))

		self.assertIsNone(self._capture(guild, folder))

	def test_prune_removes_only_expired_files(self) :
		folder = os.path.join(self.folder.name, "quick")
		os.makedirs(folder)
		old, new = os.path.join(folder, "old.txt"), os.path.join(folder, "new.txt")
		for path in (old, new) :
			with open(path, "w") as file :
				file.write("Server: x\n")
		expired = (self.now - timedelta(days=quickleaves.QUICK_LEAVE_RETENTION_DAYS + 1)).timestamp()
		os.utime(old, (expired, expired))

		self.assertEqual(quickleaves.prune(self.now, folder), 1)
		self.assertEqual(os.listdir(folder), ["new.txt"])

	def test_missing_folder(self) :
		missing = os.path.join(self.folder.name, "missing")

		self.assertEqual(quickleaves.saved_since(self.now, missing), [])
		self.assertEqual(quickleaves.prune(self.now, missing), 0)
