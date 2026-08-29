import unittest

from databases.Generators.uidgenerator import uidgenerator
from databases.current import create_bot_database, drop_bot_database
from databases.enums.loggedmessagetype import LoggedMessageType
from databases.transactions.LoggedMessageTransactions import LoggedMessageTransactions
from databases.transactions.UserTransactions import UserTransactions


class FakeGuild :
	def __init__(self, guild_id) : self.id = guild_id


class FakeChannel :
	def __init__(self, channel_id) : self.id = channel_id


class FakeMessage :
	"""Stands in for discord.Message: track only reads id, guild.id and channel.id."""

	def __init__(self, message_id, guild_id=1, channel_id=2) :
		self.id = message_id
		self.guild = FakeGuild(guild_id)
		self.channel = FakeChannel(channel_id)


class TestLoggedMessageTransactions(unittest.TestCase) :

	def setUp(self) :
		create_bot_database()
		self.lmt = LoggedMessageTransactions()
		self.ut = UserTransactions()
		self.uid = uidgenerator().create()
		self.ut.add_user_empty(self.uid)

	def tearDown(self) :
		drop_bot_database()

	def test_track_records_the_message(self) :
		self.lmt.track(FakeMessage(1001, guild_id=55, channel_id=66), self.uid, LoggedMessageType.LOBBY_LOG)
		tracked = self.lmt.get_for_user(self.uid)
		self.assertEqual(len(tracked), 1)
		self.assertEqual(tracked[0].message, 1001)
		self.assertEqual(tracked[0].guild, 55)
		self.assertEqual(tracked[0].channel, 66)
		self.assertEqual(tracked[0].type, LoggedMessageType.LOBBY_LOG)

	def test_track_keeps_the_type_it_was_given(self) :
		self.lmt.track(FakeMessage(1), self.uid, LoggedMessageType.LOBBY_LOG)
		self.lmt.track(FakeMessage(2), self.uid, LoggedMessageType.APPROVAL)
		self.lmt.track(FakeMessage(3), self.uid, LoggedMessageType.ID_CHECK)
		self.lmt.track(FakeMessage(4), self.uid, LoggedMessageType.AGE_LOG)
		types = {entry.message : entry.type for entry in self.lmt.get_for_user(self.uid)}
		self.assertEqual(types, {
			1 : LoggedMessageType.LOBBY_LOG,
			2 : LoggedMessageType.APPROVAL,
			3 : LoggedMessageType.ID_CHECK,
			4 : LoggedMessageType.AGE_LOG,
		})

	def test_track_tolerates_nothing_to_track(self) :
		# send_message returns None when the bot could not post; there is nothing to clean up.
		self.assertIsNone(self.lmt.track(None, self.uid, LoggedMessageType.LOBBY_LOG))
		self.assertEqual(self.lmt.get_for_user(self.uid), [])

	def test_track_creates_the_user_row_when_missing(self) :
		# The approval post goes out before the date of birth is stored, so the uid foreign key
		# has to be satisfied by track itself.
		fresh = uidgenerator().create()
		self.lmt.track(FakeMessage(2002), fresh, LoggedMessageType.APPROVAL)
		self.assertEqual(len(self.lmt.get_for_user(fresh)), 1)

	def test_delete_for_user_clears_only_that_user(self) :
		other = uidgenerator().create()
		self.ut.add_user_empty(other)
		self.lmt.track(FakeMessage(1), self.uid, LoggedMessageType.LOBBY_LOG)
		self.lmt.track(FakeMessage(2), other, LoggedMessageType.LOBBY_LOG)

		self.assertEqual(self.lmt.delete_for_user(self.uid), 1)
		self.assertEqual(self.lmt.get_for_user(self.uid), [])
		self.assertEqual(len(self.lmt.get_for_user(other)), 1)

	def test_rows_go_when_the_user_is_permanently_deleted(self) :
		# The GDPR purge relies on this cascade so tracked rows don't outlive the user.
		self.lmt.track(FakeMessage(3003), self.uid, LoggedMessageType.LOBBY_LOG)
		self.ut.permanent_delete(self.uid, "TestGuild")
		self.assertEqual(self.lmt.get_for_user(self.uid), [])


if __name__ == "__main__" :
	unittest.main()
