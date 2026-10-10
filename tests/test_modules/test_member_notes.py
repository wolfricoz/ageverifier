import unittest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from classes.membernotes import EMBED_FIELD_LIMIT, format_notes
from databases.Generators.guildgenerator import guildgenerator
from databases.Generators.uidgenerator import uidgenerator
from databases.current import create_bot_database, drop_bot_database
from databases.transactions.MemberNoteTransactions import MemberNoteTransactions
from databases.transactions.ServerTransactions import ServerTransactions
from databases.transactions.UserTransactions import UserTransactions

AUTHOR = 123456789012345678


class TestMemberNoteTransactions(unittest.TestCase) :

	def setUp(self) -> None :
		create_bot_database()
		self.nt = MemberNoteTransactions()
		self.uid = uidgenerator().create()
		self.gid = guildgenerator().create().guild

	def tearDown(self) -> None :
		drop_bot_database()

	def test_add_creates_a_missing_user_row(self) :
		self.assertFalse(UserTransactions().user_exists(self.uid))
		self.nt.add(self.gid, self.uid, AUTHOR, "first")
		self.assertTrue(UserTransactions().user_exists(self.uid))

	def test_add_creates_a_missing_server_row(self) :
		gid = uidgenerator().create()
		self.nt.add(gid, self.uid, AUTHOR, "unsynced guild")
		self.assertIsNotNone(ServerTransactions().get(gid))

	def test_notes_are_newest_first_and_scoped_to_the_guild(self) :
		other_gid = guildgenerator().create().guild
		first = self.nt.add(self.gid, self.uid, AUTHOR, "first")
		second = self.nt.add(self.gid, self.uid, AUTHOR, "second")
		self.nt.add(other_gid, self.uid, AUTHOR, "other server")

		notes = self.nt.get_for_member(self.gid, self.uid)
		self.assertEqual([note.id for note in notes], [second.id, first.id])
		self.assertEqual(self.nt.count_for_member(self.gid, self.uid), 2)
		self.assertEqual([note.id for note in self.nt.get_for_member(self.gid, self.uid, limit=1)], [second.id])

	def test_remove_is_scoped_to_the_guild(self) :
		other_gid = guildgenerator().create().guild
		note = self.nt.add(self.gid, self.uid, AUTHOR, "keep me")

		self.assertFalse(self.nt.remove(other_gid, note.id))
		self.assertEqual(self.nt.count_for_member(self.gid, self.uid), 1)
		self.assertTrue(self.nt.remove(self.gid, note.id))
		self.assertEqual(self.nt.count_for_member(self.gid, self.uid), 0)

	def test_count_for_user_counts_every_guild(self) :
		other_gid = guildgenerator().create().guild
		self.assertEqual(self.nt.count_for_user(self.uid), 0)
		self.nt.add(self.gid, self.uid, AUTHOR, "one")
		self.nt.add(other_gid, self.uid, AUTHOR, "two")
		self.assertEqual(self.nt.count_for_user(self.uid), 2)

	def test_notes_go_with_the_user_on_permanent_delete(self) :
		self.nt.add(self.gid, self.uid, AUTHOR, "gone after removal")
		UserTransactions().permanent_delete(self.uid, "GDPR Removal (30 days passed)")
		self.assertEqual(self.nt.count_for_user(self.uid), 0)

	def test_notes_go_with_the_server(self) :
		self.nt.add(self.gid, self.uid, AUTHOR, "gone with the server")
		ServerTransactions().delete(self.gid)
		self.assertEqual(self.nt.count_for_user(self.uid), 0)


def note(text: str, author: int = AUTHOR) :
	return SimpleNamespace(text=text, author=author, created_at=datetime.now(tz=timezone.utc) - timedelta(days=1))


class TestFormatNotes(unittest.TestCase) :

	def test_no_notes_skips_the_field(self) :
		self.assertIsNone(format_notes([]))
		self.assertIsNone(format_notes(None))

	def test_lists_each_note_with_its_author(self) :
		value = format_notes([note("watch for alts"), note("asked about rules", author=42)])
		self.assertIn("watch for alts", value)
		self.assertIn("<@42>", value)
		self.assertNotIn("more", value)

	def test_points_to_the_full_list_when_more_exist(self) :
		value = format_notes([note("a"), note("b")], total=5)
		self.assertTrue(value.endswith("+3 more, see `/notes list`"))

	def test_stays_under_the_embed_field_limit(self) :
		value = format_notes([note("x" * 500), note("y" * 500), note("z" * 500)], total=4)
		self.assertLessEqual(len(value), EMBED_FIELD_LIMIT)
		self.assertTrue(value.endswith("+1 more, see `/notes list`"))

	def test_long_notes_without_more_still_point_to_the_list(self) :
		value = format_notes([note("x" * 500), note("y" * 500), note("z" * 500)])
		self.assertLessEqual(len(value), EMBED_FIELD_LIMIT)
		self.assertIn("/notes list", value)


if __name__ == '__main__' :
	unittest.main()
