import unittest
from unittest import mock

import discord

from classes.AgeCalculations import AgeCalculations
from classes.permissions_notice import PermissionNotice
from databases.transactions.ConfigData import ConfigData


class FakeOwner :
	pass


class FakeGuild :
	"""Stands in for discord.Guild: get_channel() is the cache, fetch_channel() the API."""

	def __init__(self, guild_id=1, cached=None, fetch_side_effect=None) :
		self.id = guild_id
		self.name = "Test guild"
		self.owner = FakeOwner()
		self.cached = cached or {}
		self.fetch_calls = 0
		self.fetch_side_effect = fetch_side_effect

	def get_channel(self, channel_id) :
		return self.cached.get(channel_id)

	async def fetch_channel(self, channel_id) :
		self.fetch_calls += 1
		if self.fetch_side_effect :
			raise self.fetch_side_effect
		return f"channel-{channel_id}"


def not_found() :
	return discord.NotFound(mock.Mock(status=404, reason="Not Found"), "Unknown Channel")


def server_error() :
	return discord.DiscordServerError(mock.Mock(status=503, reason="Service Unavailable"), "upstream")


class TestGetChannelId(unittest.TestCase) :
	"""Channel ids are stored as strings, and unset ones sometimes as the literal "None" (AGEVERIFIER-E1)."""

	def setUp(self) :
		self.config = ConfigData()
		self.config.conf[1] = {}

	def tearDown(self) :
		self.config.conf.pop(1, None)

	def test_numeric_string_is_int(self) :
		self.config.conf[1]["INVITE_LOG"] = "1234"
		self.assertEqual(self.config.get_channel_id(1, "invite_log"), 1234)

	def test_int_is_kept(self) :
		self.config.conf[1]["INVITE_LOG"] = 1234
		self.assertEqual(self.config.get_channel_id(1, "invite_log"), 1234)

	def test_unset_values_are_none(self) :
		for value in ("None", "", "  ", None, "abc") :
			self.config.conf[1]["INVITE_LOG"] = value
			self.assertIsNone(self.config.get_channel_id(1, "invite_log"), value)

	def test_missing_key_is_none(self) :
		self.assertIsNone(self.config.get_channel_id(1, "invite_log"))


class TestGetChannel(unittest.IsolatedAsyncioTestCase) :
	"""get_channel() must give up on a deleted channel instead of retrying forever (AGEVERIFIER-HY)."""

	def setUp(self) :
		self.config = ConfigData()
		self.config.conf[1] = {"SERVER_JOIN_CHANNEL" : "55"}
		PermissionNotice._last_sent.clear()
		patcher = mock.patch("databases.transactions.ConfigData.send_message", new=mock.AsyncMock())
		self.send_message = patcher.start()
		self.addCleanup(patcher.stop)
		sleeper = mock.patch("databases.transactions.ConfigData.asyncio.sleep", new=mock.AsyncMock())
		sleeper.start()
		self.addCleanup(sleeper.stop)

	def tearDown(self) :
		self.config.conf.pop(1, None)
		PermissionNotice._last_sent.clear()

	async def test_cached_channel(self) :
		guild = FakeGuild(cached={55 : "cached"})
		self.assertEqual(await self.config.get_channel(guild, "server_join_channel"), "cached")
		self.assertEqual(guild.fetch_calls, 0)

	async def test_fetches_uncached_channel(self) :
		guild = FakeGuild()
		self.assertEqual(await self.config.get_channel(guild, "server_join_channel"), "channel-55")

	async def test_deleted_channel_is_fetched_once(self) :
		guild = FakeGuild(fetch_side_effect=not_found())
		self.assertIsNone(await self.config.get_channel(guild, "server_join_channel"))
		self.assertEqual(guild.fetch_calls, 1)

	async def test_server_errors_are_retried_three_times(self) :
		guild = FakeGuild(fetch_side_effect=server_error())
		self.assertIsNone(await self.config.get_channel(guild, "server_join_channel"))
		self.assertEqual(guild.fetch_calls, 3)

	async def test_owner_is_notified_once_per_hour(self) :
		self.config.conf[1]["SERVER_JOIN_CHANNEL"] = "None"
		guild = FakeGuild()
		for _ in range(3) :
			self.assertIsNone(await self.config.get_channel(guild, "server_join_channel"))
		self.send_message.assert_awaited_once()
		self.assertEqual(self.send_message.await_args.kwargs.get("error_mode"), "ignore")

	async def test_failed_owner_notice_does_not_raise(self) :
		self.config.conf[1]["SERVER_JOIN_CHANNEL"] = "None"
		self.send_message.side_effect = AttributeError("'Member' object has no attribute 'permissions_for'")
		self.assertIsNone(await self.config.get_channel(FakeGuild(), "server_join_channel"))


class TestDobToAge(unittest.TestCase) :
	"""dob_to_age() accepts the same separators as dob_regex() (AGEVERIFIER-D7)."""

	def test_separators(self) :
		expected = AgeCalculations.dob_to_age("03/11/2002")
		for dob in ("03-11-2002", "03.11.2002", " 03/11/2002 ") :
			self.assertEqual(AgeCalculations.dob_to_age(dob), expected, dob)


if __name__ == '__main__' :
	unittest.main()
