"""Background work for a server the bot was just removed from, or that Discord rate limits,
must not stop the loop for every other server."""
import unittest
from unittest import mock

import discord

from modules import Tasks as tasks_module
from modules.inviteinfo import inviteInfo


def http_error(cls, status, message) :
	response = mock.MagicMock(status=status, reason=message)
	return cls(response, message)


class TestConfigReload(unittest.IsolatedAsyncioTestCase) :

	async def test_unknown_guild_does_not_stop_the_reload(self) :
		gone = mock.MagicMock(invites=mock.AsyncMock(side_effect=http_error(discord.NotFound, 404, "Unknown Guild")))
		alive = mock.MagicMock(id=2, invites=mock.AsyncMock(return_value=["invite"]))
		cog = mock.MagicMock()
		cog.bot.guilds = [gone, alive]
		cog.bot.invites = {}
		with mock.patch.object(tasks_module, "ConfigData") as config, \
				mock.patch.object(tasks_module, "AccessControl") :
			config.return_value.load_all_guilds = mock.AsyncMock()
			await tasks_module.Tasks.config_reload.coro(cog)
		self.assertEqual(cog.bot.invites, {2 : ["invite"]})


class TestUpdateInvites(unittest.IsolatedAsyncioTestCase) :

	async def test_a_failing_server_is_skipped(self) :
		cog = mock.MagicMock()
		cog.update_invites.current_loop = 1
		servers = [mock.MagicMock(guild=1, invite=None), mock.MagicMock(guild=2, invite=None)]
		check = mock.AsyncMock(side_effect=[AttributeError("'NoneType' object has no attribute 'permissions_for'"),
		                                    "https://discord.gg/abc"])
		with mock.patch.object(tasks_module, "ServerTransactions") as servers_db, \
				mock.patch.object(tasks_module, "check_guild_invites", check) :
			servers_db.return_value.get_invalid_invites.return_value = servers
			await tasks_module.Tasks.update_invites.coro(cog)
		servers_db.return_value.update.assert_called_once()
		self.assertEqual(servers_db.return_value.update.call_args.args[0], 2)


class TestInvitesOnMemberRemove(unittest.IsolatedAsyncioTestCase) :

	async def test_rate_limit_is_not_raised(self) :
		member = mock.MagicMock()
		member.guild.invites = mock.AsyncMock(side_effect=http_error(discord.HTTPException, 429, "You are being rate limited."))
		cog = inviteInfo(mock.MagicMock(invites={}))
		await cog.on_member_remove(member)
		self.assertEqual(cog.bot.invites, {})
