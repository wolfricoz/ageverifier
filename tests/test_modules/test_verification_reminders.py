import asyncio
import unittest
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from classes.verification import reminders
from resources.data.config_variables import VerificationMethods

PREMIUM_GID = 1
FREE_GID = 2


def entry(gid: int, opened_minutes_ago: int, uuid: str) :
	return SimpleNamespace(uuid=uuid, uid=10, gid=gid, opened=datetime.now() - timedelta(minutes=opened_minutes_ago))


class TestVerificationReminders(unittest.TestCase) :
	"""send_abandoned_reminders with the database, config and Discord mocked out."""

	def run_reminders(self, entries, minutes=30, in_lobby=True, member_found=True,
	                  method=VerificationMethods.WEBSITE) :
		transactions = MagicMock()
		transactions.get_abandoned.return_value = entries
		access = MagicMock(premium_guilds=[PREMIUM_GID])
		access.is_premium.side_effect = lambda gid : gid == PREMIUM_GID
		config = MagicMock()
		config.get_key_int_or_zero.return_value = minutes
		config.get_key.return_value = method
		member = MagicMock() if member_found else None
		queue = MagicMock()
		bot = MagicMock()
		bot.get_guild.side_effect = lambda gid : SimpleNamespace(id=gid)

		with patch.object(reminders, "WebsiteDataTransactions", return_value=transactions), \
				patch.object(reminders, "AccessControl", return_value=access), \
				patch.object(reminders, "ConfigData", return_value=config), \
				patch.object(reminders, "fetch_member", AsyncMock(return_value=member)), \
				patch.object(reminders, "still_in_lobby", return_value=in_lobby), \
				patch.object(reminders, "send_reminder", MagicMock()), \
				patch.object(reminders, "Queue", return_value=queue) :
			sent = asyncio.run(reminders.send_abandoned_reminders(bot))
		reminded = [call.args[0] for call in transactions.set_reminded.call_args_list]
		return sent, reminded, queue

	def test_reminds_premium_link_past_delay(self) :
		sent, reminded, queue = self.run_reminders([entry(PREMIUM_GID, 45, "a")])

		self.assertEqual(sent, 1)
		self.assertEqual(reminded, ["a"])
		queue.add.assert_called_once()

	def test_waits_until_delay_has_passed(self) :
		sent, reminded, _ = self.run_reminders([entry(PREMIUM_GID, 10, "a")])

		self.assertEqual((sent, reminded), (0, []))

	def test_skips_free_guilds_without_marking(self) :
		# Not marked, so the link is still reminded if the guild becomes premium soon after.
		sent, reminded, _ = self.run_reminders([entry(FREE_GID, 45, "a")])

		self.assertEqual((sent, reminded), (0, []))

	def test_disabled_reminder_sends_nothing(self) :
		sent, reminded, _ = self.run_reminders([entry(PREMIUM_GID, 45, "a")], minutes=0)

		self.assertEqual((sent, reminded), (0, []))

	def test_marks_but_skips_members_who_left_or_are_verified(self) :
		for kwargs in ({"member_found" : False}, {"in_lobby" : False},
		               {"method" : VerificationMethods.BASIC}) :
			with self.subTest(**{k : str(v) for k, v in kwargs.items()}) :
				sent, reminded, queue = self.run_reminders([entry(PREMIUM_GID, 45, "a")], **kwargs)

				self.assertEqual((sent, reminded), (0, ["a"]))
				queue.add.assert_not_called()


if __name__ == '__main__' :
	unittest.main()
