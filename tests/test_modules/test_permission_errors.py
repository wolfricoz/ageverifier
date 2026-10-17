import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import discord
from discord_py_utilities.exceptions import NoPermissionException

import classes.helpers as helpers
import modules.logs as logs
from classes import idcheck, lobbyprocess
from classes.configsetup import ConfigSetup
from classes.lobby import Clean

GUILD_ID = 321


def forbidden() :
	return discord.Forbidden(MagicMock(status=403), "Missing Permissions")


class TestAutoKick(unittest.TestCase) :
	"""IdCheck.auto_kick with the discrepancy kick toggle on."""

	def kick(self, missing=(), kick_error=None) :
		guild = MagicMock(id=GUILD_ID)
		member = MagicMock(kick=AsyncMock(side_effect=kick_error))
		channel = MagicMock(send=AsyncMock())
		config = MagicMock()
		config.get_toggle.side_effect = lambda guild_id, key : key == "AUTOKICK_ON_DISCREPANCY"
		notify, send = AsyncMock(), AsyncMock()
		with patch.object(idcheck, "ConfigData", return_value=config), \
				patch.object(idcheck, "check_missing_guild_permissions", return_value=list(missing)), \
				patch.object(idcheck, "send_message", send), \
				patch.object(idcheck.PermissionNotice, "notify", notify) :
			asyncio.run(idcheck.IdCheck.auto_kick(member, "mismatch", guild, channel, "reason"))
		return member, channel, notify, send

	def test_kicks_and_tells_staff(self) :
		member, channel, notify, send = self.kick()

		member.kick.assert_awaited_once()
		channel.send.assert_awaited_once()
		notify.assert_not_awaited()

	def test_without_kick_members_tells_staff_and_does_not_dm_the_member(self) :
		member, channel, notify, send = self.kick(missing=["kick_members"])

		self.assertEqual(notify.await_args.kwargs["missing"], ["kick_members"])
		send.assert_not_awaited()
		member.kick.assert_not_awaited()
		channel.send.assert_not_awaited()

	def test_a_refused_kick_tells_staff_instead_of_raising(self) :
		member, channel, notify, send = self.kick(kick_error=forbidden())

		notify.assert_awaited_once()
		channel.send.assert_not_awaited()


class TestCleanLobby(unittest.TestCase) :
	def clean(self, channel_missing=(), guild_missing=()) :
		bot = MagicMock()
		bot.user = MagicMock(spec=discord.Member, bot=True)
		waiting = MagicMock(spec=discord.Member, global_name="waiting")
		waiting.guild_permissions.manage_messages = False
		message = MagicMock(author=bot.user, mentions=[waiting])

		async def history(**kwargs) :
			yield message

		lobby = MagicMock(history=history)
		guild = MagicMock(id=GUILD_ID)
		guild.get_channel_or_thread.return_value = lobby
		config = MagicMock()
		config.get_key_int_or_zero.return_value = 7
		queue = MagicMock()
		notify, report = AsyncMock(), AsyncMock()

		def missing_in_channel(channel, perms) :
			return [perm for perm in perms if perm in channel_missing]

		with patch.object(Clean, "DEBUG", None), \
				patch.object(Clean, "ConfigData", return_value=config), \
				patch.object(Clean, "ServerTransactions"), \
				patch.object(Clean, "Queue", return_value=queue), \
				patch.object(Clean, "check_missing_channel_permissions", side_effect=missing_in_channel), \
				patch.object(Clean, "check_missing_guild_permissions", return_value=list(guild_missing)), \
				patch.object(Clean, "send_to_channel", report), \
				patch.object(Clean.PermissionNotice, "notify", notify) :
			asyncio.run(Clean.clean_lobby(bot, guild))
		return waiting, queue, notify, report

	def test_kicks_and_cleans_with_every_permission(self) :
		waiting, queue, notify, report = self.clean()

		waiting.kick.assert_called_once()
		self.assertEqual(queue.add.call_count, 3)  # removal DM, kick, message delete
		notify.assert_not_awaited()

	def test_stops_when_it_cannot_read_the_lobby(self) :
		waiting, queue, notify, report = self.clean(channel_missing=["read_message_history"])

		self.assertEqual(notify.await_args.kwargs["missing"], ["read_message_history"])
		queue.add.assert_not_called()
		report.assert_not_awaited()

	def test_skips_kicks_and_says_so_without_kick_members(self) :
		waiting, queue, notify, report = self.clean(guild_missing=["kick_members"])

		self.assertEqual(notify.await_args.kwargs["missing"], ["kick_members"])
		waiting.kick.assert_not_called()
		waiting.send.assert_not_called()
		self.assertIn("Skipped kicks", report.await_args.args[3])

	def test_skips_message_removal_without_manage_messages(self) :
		waiting, queue, notify, report = self.clean(channel_missing=["manage_messages"])

		waiting.kick.assert_called_once()
		self.assertEqual(queue.add.call_count, 2)  # removal DM and kick only
		self.assertIn("Skipped message removal", report.await_args.args[3])


class TestVerifiedWelcome(unittest.TestCase) :
	def test_tells_staff_when_the_welcome_channel_refuses_the_message(self) :
		guild = MagicMock(id=GUILD_ID)
		channel = MagicMock()
		guild.get_channel_or_thread.return_value = channel
		config = MagicMock()
		config.get_toggle.side_effect = lambda guild_id, key, *args : key == "send_verification_completed_message"
		config.get_channel_id.return_value = 55
		notify = AsyncMock()
		with patch.object(lobbyprocess, "ConfigData", return_value=config), \
				patch.object(lobbyprocess, "send_message", AsyncMock(side_effect=NoPermissionException(["send_messages"]))), \
				patch.object(lobbyprocess.PermissionNotice, "notify", notify) :
			asyncio.run(lobbyprocess.LobbyProcess.welcome(MagicMock(), guild))

		notify.assert_awaited_once()
		self.assertIs(notify.await_args.kwargs["channel"], channel)


class TestJoinHelpers(unittest.TestCase) :
	def test_refused_join_roles_tell_staff(self) :
		member = MagicMock(add_roles=AsyncMock(side_effect=forbidden()))
		config = MagicMock()
		config.get_key_or_none.return_value = ["1"]
		notify = AsyncMock()
		with patch.object(helpers, "ConfigData", return_value=config), \
				patch.object(helpers.PermissionNotice, "notify", notify) :
			result = asyncio.run(helpers.add_join_roles(member))

		self.assertFalse(result)
		self.assertEqual(notify.await_args.kwargs["missing"], ["manage_roles"])

	def test_a_lobby_the_bot_cannot_post_in_tells_staff(self) :
		member = MagicMock()
		lobby = MagicMock()
		member.guild.get_channel_or_thread.return_value = lobby
		config = MagicMock()
		config.get_key.return_value = "enabled"
		notify, send = AsyncMock(), AsyncMock()
		with patch.object(helpers, "ConfigData", return_value=config), \
				patch.object(helpers, "JoinHistoryTransactions"), \
				patch.object(helpers, "add_join_roles", AsyncMock()), \
				patch.object(helpers, "check_missing_channel_permissions", return_value=["embed_links"]), \
				patch.object(helpers, "send_message", send), \
				patch.object(helpers.PermissionNotice, "notify", notify) :
			asyncio.run(helpers.welcome_user(member))

		self.assertIs(notify.await_args.kwargs["channel"], lobby)
		send.assert_not_awaited()


class TestAutoSetup(unittest.TestCase) :
	def test_stops_before_confirming_without_manage_channels(self) :
		interaction = MagicMock()
		respond = AsyncMock()
		with patch("classes.configsetup.check_missing_guild_permissions", return_value=["manage_channels"]), \
				patch("classes.configsetup.confirmAction") as confirm, \
				patch("classes.configsetup.PermissionNotice.respond", respond) :
			result = asyncio.run(ConfigSetup().auto(interaction, {}, {}, {}))

		self.assertFalse(result)
		self.assertEqual(respond.await_args.kwargs["missing"], ["manage_channels"])
		confirm.assert_not_called()


class TestForbiddenCommandMessage(unittest.TestCase) :
	def test_names_the_channel_and_what_is_missing(self) :
		channel = MagicMock(spec=discord.TextChannel)
		channel.name = "lobby"
		with patch.object(logs, "check_missing_channel_permissions", return_value=["embed_links"]) :
			message = logs._forbidden_message(channel)

		self.assertIn("#lobby", message)
		self.assertIn("Embed Links", message)

	def test_points_at_the_permission_check_otherwise(self) :
		with patch.object(logs, "check_missing_channel_permissions", return_value=[]) :
			message = logs._forbidden_message(MagicMock(spec=discord.TextChannel))

		self.assertIn("/config permissioncheck", message)


if __name__ == '__main__' :
	unittest.main()
