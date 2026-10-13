import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import discord

import modules.Lobby as lobby_module
from classes.AgeCalculations import AgeCalculations
from classes.config.utils import format_config_value
from classes.text import plural
from resources.data.config_variables import config_title, is_required_key


class TestDayFirstDates(unittest.TestCase) :

	def test_unambiguous_day_first_is_swapped(self) :
		self.assertEqual(AgeCalculations.swap_day_first("18/06/1997"), "06/18/1997")
		self.assertEqual(AgeCalculations.swap_day_first("31-12-2000"), "12-31-2000")

	def test_month_first_and_ambiguous_dates_are_left_alone(self) :
		for value in ["06/18/1997", "05/06/1997", "13/13/2000", "18/06-1997", "not a date"] :
			self.assertEqual(AgeCalculations.swap_day_first(value), value)

	def test_dob_regex_accepts_day_first(self) :
		self.assertEqual(AgeCalculations.dob_regex("18/06/1997"), "06/18/1997")

	def test_validate_dob_accepts_day_first(self) :
		self.assertIsNotNone(AgeCalculations.validate_dob("18/06/1997"))


class TestConfigWording(unittest.TestCase) :

	def test_channels_and_roles_become_mentions(self) :
		self.assertEqual(format_config_value("server_join_channel", "123"), "<#123>")
		self.assertEqual(format_config_value("VERIFICATION_ADD_ROLE", [1, "2"]), "<@&1>, <@&2>")

	def test_other_values_and_unset(self) :
		self.assertEqual(format_config_value("cooldown", 5), "5")
		self.assertEqual(format_config_value("leave_log", "None"), "not set")

	def test_titles_and_required_keys(self) :
		self.assertEqual(config_title("server_join_channel"), "Lobby channel")
		self.assertEqual(config_title("SOME_NEW_KEY"), "Some new key")
		self.assertTrue(is_required_key("APPROVAL_CHANNEL"))
		self.assertFalse(is_required_key("leave_log"))

	def test_plural(self) :
		self.assertEqual(plural(1, "day"), "1 day")
		self.assertEqual(plural(3, "day"), "3 days")


class TestRaidPurge(unittest.TestCase) :

	def purge(self, dry_run) :
		member = MagicMock(spec=discord.Member, id=1)
		member.name = "raider"
		message = MagicMock(author=MagicMock(bot=True), mentions=[member], delete=AsyncMock())

		async def history(**kwargs) :
			yield message

		lobby = MagicMock(history=history)
		interaction = MagicMock()
		interaction.guild.get_channel.return_value = lobby
		interaction.followup.send = AsyncMock()
		send = AsyncMock()
		# Cancelled, so the test never reaches the kicks.
		confirm = MagicMock(return_value=MagicMock(send_message=AsyncMock(), wait=AsyncMock(), confirmed=False))
		with patch.object(lobby_module, "ConfigData"), \
				patch.object(lobby_module, "check_missing_channel_permissions", return_value=[]), \
				patch.object(lobby_module, "check_missing_guild_permissions", return_value=[]), \
				patch.object(lobby_module, "send_response", send), \
				patch.object(lobby_module, "confirmAction", confirm) :
			asyncio.run(lobby_module.Lobby.raid_purge.callback(MagicMock(), interaction, 1, dry_run))
		return member, send, confirm

	def test_dry_run_lists_without_kicking(self) :
		member, send, confirm = self.purge(True)
		self.assertIn("Dry run: a purge would kick 1 member who joined in the last 1 day: raider.", send.await_args.args[1])
		member.kick.assert_not_called()
		confirm.assert_not_called()

	def test_confirmation_names_the_count(self) :
		member, send, confirm = self.purge(False)
		prompt = confirm.return_value.send_message.await_args.args[1]
		self.assertIn("**1 member**", prompt)
		self.assertIn("raider", prompt)
		member.kick.assert_not_called()


if __name__ == '__main__' :
	unittest.main()
