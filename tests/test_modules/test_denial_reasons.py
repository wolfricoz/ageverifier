import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock

import discord

from classes.denialreasons import DM_LIMIT, denial_message, fill_placeholders, send_denial
from databases.Generators.guildgenerator import guildgenerator
from databases.Generators.uidgenerator import uidgenerator
from databases.current import create_bot_database, drop_bot_database
from databases.transactions.DenialReasonTransactions import DenialReasonTransactions
from databases.transactions.ServerTransactions import ServerTransactions
from resources.data.config_variables import DEFAULT_DENIAL_REASONS, MAX_DENIAL_LABEL_LENGTH, MAX_DENIAL_REASONS
from views.select.denialreasonselect import CUSTOM_VALUE, DESCRIPTION_LENGTH, DenialReasonView


class TestDenialReasonTransactions(unittest.TestCase) :

	def setUp(self) -> None :
		create_bot_database()
		self.dt = DenialReasonTransactions()
		self.gid = guildgenerator().create().guild

	def tearDown(self) -> None :
		drop_bot_database()

	def test_a_new_guild_gets_the_defaults(self) :
		reasons = self.dt.get_for_guild(self.gid)
		self.assertEqual([(r.label, r.message) for r in reasons], list(DEFAULT_DENIAL_REASONS))
		# Seeded once: reading again doesn't add a second set.
		self.assertEqual(len(self.dt.get_for_guild(self.gid)), len(DEFAULT_DENIAL_REASONS))

	def test_seeding_creates_a_missing_server_row(self) :
		gid = uidgenerator().create()
		self.dt.get_for_guild(gid)
		self.assertIsNotNone(ServerTransactions().get(gid))

	def test_seeding_twice_keeps_one_set(self) :
		self.dt.get_for_guild(self.gid)
		self.dt._seed_defaults(self.gid)
		self.assertEqual(self.dt.count(self.gid), len(DEFAULT_DENIAL_REASONS))

	def test_add_update_and_remove_are_scoped_to_the_guild(self) :
		other_gid = guildgenerator().create().guild
		reason = self.dt.add(self.gid, "  Blurry ID  ", " Please send a sharper photo. ")
		self.assertEqual((reason.label, reason.message), ("Blurry ID", "Please send a sharper photo."))

		self.assertIsNone(self.dt.get(other_gid, reason.id))
		self.assertFalse(self.dt.update(other_gid, reason.id, "Hijacked", "nope"))
		self.assertFalse(self.dt.remove(other_gid, reason.id))

		self.assertTrue(self.dt.update(self.gid, reason.id, "Blurry photo", "Retake it in daylight."))
		self.assertEqual(self.dt.get(self.gid, reason.id).label, "Blurry photo")
		self.assertTrue(self.dt.remove(self.gid, reason.id))
		self.assertIsNone(self.dt.get(self.gid, reason.id))

	def test_label_taken_ignores_case_and_the_preset_being_edited(self) :
		reason = self.dt.add(self.gid, "Blurry ID", "message")
		self.assertTrue(self.dt.label_taken(self.gid, "blurry id "))
		self.assertFalse(self.dt.label_taken(self.gid, "Blurry ID", exclude_id=reason.id))
		self.assertFalse(self.dt.label_taken(guildgenerator().create().guild, "Blurry ID"))

	def test_reset_restores_the_defaults(self) :
		self.dt.get_for_guild(self.gid)
		self.dt.add(self.gid, "Custom", "message")
		reasons = self.dt.reset(self.gid)
		self.assertEqual([r.label for r in reasons], [label for label, _ in DEFAULT_DENIAL_REASONS])

	def test_reasons_go_with_the_server(self) :
		self.dt.get_for_guild(self.gid)
		ServerTransactions().delete(self.gid)
		self.assertEqual(self.dt.count(self.gid), 0)


def fake_user(user_id: int = 42) :
	return SimpleNamespace(id=user_id, mention=f"<@{user_id}>", send=AsyncMock())


GUILD = SimpleNamespace(id=1, name="Test Server")


class TestDenialMessage(unittest.TestCase) :

	def test_placeholders_are_filled(self) :
		text = fill_placeholders("Hi {user}, welcome back to {server}.", fake_user(), GUILD)
		self.assertEqual(text, "Hi <@42>, welcome back to Test Server.")

	def test_other_braces_are_left_alone(self) :
		self.assertEqual(fill_placeholders("{0.__class__} {name}", fake_user(), GUILD), "{0.__class__} {name}")

	def test_message_explains_the_reason(self) :
		text = denial_message("Invalid date of birth", "Use mm/dd/yyyy.", fake_user(), GUILD)
		self.assertIn("Test Server", text)
		self.assertIn("**Reason:** Invalid date of birth", text)
		self.assertIn("Use mm/dd/yyyy.", text)

	def test_message_stays_under_the_dm_limit(self) :
		guild = SimpleNamespace(id=1, name="x" * 100)
		text = denial_message("y" * MAX_DENIAL_LABEL_LENGTH, "{server}" * 187, fake_user(), guild)
		self.assertLessEqual(len(text), DM_LIMIT)
		self.assertIn("Replies to this message are not read", text)


class TestSendDenial(unittest.IsolatedAsyncioTestCase) :

	async def test_delivered(self) :
		user = fake_user()
		self.assertTrue(await send_denial(user, GUILD, "Reason", "Message"))
		user.send.assert_awaited_once()

	async def test_closed_dms_are_skipped(self) :
		user = fake_user()
		user.send.side_effect = discord.Forbidden(SimpleNamespace(status=403, reason="Forbidden"), "Cannot send messages to this user")
		self.assertFalse(await send_denial(user, GUILD, "Reason", "Message"))


class TestDenialReasonView(unittest.IsolatedAsyncioTestCase) :

	@staticmethod
	def reasons(count: int) :
		return [SimpleNamespace(id=i, label=f"Reason {i}", message="word " * 60) for i in range(count)]

	async def test_custom_reason_is_always_offered(self) :
		view = DenialReasonView(self.reasons(3), AsyncMock())
		values = [option.value for option in view.select.options]
		self.assertEqual(values, ["0", "1", "2", CUSTOM_VALUE])
		self.assertTrue(all(len(option.description) <= DESCRIPTION_LENGTH for option in view.select.options))

	async def test_options_fit_in_one_select(self) :
		view = DenialReasonView(self.reasons(30), AsyncMock())
		self.assertEqual(len(view.select.options), MAX_DENIAL_REASONS + 1)

	async def test_only_the_first_pick_counts(self) :
		on_pick = AsyncMock()
		view = DenialReasonView(self.reasons(1), on_pick)
		second = SimpleNamespace(response=SimpleNamespace(send_message=AsyncMock()))
		await view.finish(SimpleNamespace(), "Reason 0", "message")
		await view.finish(second, "Reason 0", "message")
		on_pick.assert_awaited_once()
		second.response.send_message.assert_awaited_once()


if __name__ == '__main__' :
	unittest.main()
