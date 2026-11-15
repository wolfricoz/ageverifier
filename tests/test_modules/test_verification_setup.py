import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import discord

from classes.permissions_notice import PermissionNotice
from classes.verification import process, setup_check
from resources.data.config_variables import is_required_key
from views.buttons import reverifybutton, verifybutton

GUILD_ID = 4242


def config_with(**values) :
	config = MagicMock()
	config.get_key_int_or_zero.side_effect = lambda guild_id, key : values.get(key, 0)
	return config


def guild_mock() :
	guild = MagicMock(id=GUILD_ID)
	guild.name = "Test Server"
	guild.owner = MagicMock(send=AsyncMock())
	return guild


class TestMissingSettings(unittest.TestCase) :

	def test_lists_only_the_unset_channels(self) :
		with patch.object(setup_check, "ConfigData", return_value=config_with(approval_channel=1)) :
			self.assertEqual(setup_check.missing_verification_settings(GUILD_ID), ["verification_failure_log"])

	def test_nothing_missing_when_both_set(self) :
		with patch.object(setup_check, "ConfigData", return_value=config_with(approval_channel=1, verification_failure_log=2)) :
			self.assertEqual(setup_check.missing_verification_settings(GUILD_ID), [])

	def test_member_message_names_the_setting_by_title(self) :
		message = setup_check.member_message(["verification_failure_log"])
		self.assertIn("Failed verification log", message)
		self.assertIn("`verification_failure_log`", message)
		self.assertNotIn("unknown error", message)

	def test_failure_log_is_marked_required_in_setup(self) :
		self.assertTrue(is_required_key("verification_failure_log"))


class TestVerifyWithoutSetup(unittest.TestCase) :
	"""VerificationProcess.verify on a server missing the failed verification log."""

	def test_member_gets_a_setup_message_and_staff_are_told(self) :
		guild = guild_mock()
		member = MagicMock(id=7)
		vp = process.VerificationProcess(MagicMock(), member, guild, "1", "1", "1990", 30)
		notify = AsyncMock()
		with patch.object(setup_check, "ConfigData", return_value=config_with(approval_channel=1)), \
				patch.object(process, "UserTransactions"), \
				patch.object(process, "notify_staff", notify) :
			result = asyncio.run(vp.verify())

		self.assertEqual(result, vp.error)
		self.assertIn("Failed verification log", vp.error)
		self.assertNotIn("unknown error", vp.error)
		notify.assert_awaited_once_with(guild, ["verification_failure_log"])


class TestNotifyStaff(unittest.TestCase) :

	def setUp(self) :
		PermissionNotice._last_sent.pop(GUILD_ID, None)

	def tearDown(self) :
		PermissionNotice._last_sent.pop(GUILD_ID, None)

	def notify(self, guild, **config) :
		with patch.object(setup_check, "ConfigData", return_value=config_with(**config)), \
				patch.object(setup_check, "find_first_accessible_text_channel", return_value=None) :
			return asyncio.run(setup_check.notify_staff(guild, ["verification_failure_log"]))

	def test_posts_in_the_approval_channel_once_an_hour(self) :
		guild = guild_mock()
		mod_channel = MagicMock(send=AsyncMock())
		guild.get_channel_or_thread.return_value = mod_channel

		self.assertTrue(self.notify(guild, approval_channel=1))
		self.assertFalse(self.notify(guild, approval_channel=1))

		mod_channel.send.assert_awaited_once()
		self.assertIn("Failed verification log", mod_channel.send.await_args.kwargs["content"])
		self.assertIn("Test Server", mod_channel.send.await_args.kwargs["content"])
		guild.owner.send.assert_not_awaited()

	def test_falls_back_to_the_owner_when_the_channel_refuses(self) :
		guild = guild_mock()
		guild.get_channel_or_thread.return_value = MagicMock(
			send=AsyncMock(side_effect=discord.Forbidden(MagicMock(status=403), "Missing Permissions")))

		self.assertTrue(self.notify(guild, approval_channel=1))
		guild.owner.send.assert_awaited_once()

	def test_never_raises(self) :
		guild = guild_mock()
		guild.get_channel_or_thread.side_effect = RuntimeError("boom")
		self.assertFalse(self.notify(guild, approval_channel=1))


class TestVerifyButtonsStopEarly(unittest.TestCase) :
	"""The verify buttons tell the member before they fill in the modal."""

	def check(self, module, view) :
		interaction = MagicMock()
		interaction.guild = guild_mock()
		send, notify = AsyncMock(), AsyncMock()
		with patch.object(module, "missing_verification_settings", return_value=["verification_failure_log"]), \
				patch.object(module, "send_response", send), \
				patch.object(module, "notify_staff", notify) :
			handled = asyncio.run(view.id_verified_check(interaction))
		return handled, send, notify

	def test_verify_button(self) :
		handled, send, notify = self.check(verifybutton, verifybutton.VerifyButton.__new__(verifybutton.VerifyButton))
		self.assertTrue(handled)
		self.assertIn("Failed verification log", send.await_args.args[1])
		notify.assert_awaited_once()

	def test_reverify_button(self) :
		handled, send, notify = self.check(reverifybutton, reverifybutton.ReVerifyButton.__new__(reverifybutton.ReVerifyButton))
		self.assertTrue(handled)
		self.assertIn("Failed verification log", send.await_args.args[1])
		notify.assert_awaited_once()


if __name__ == "__main__" :
	unittest.main()
