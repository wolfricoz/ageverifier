import unittest
from unittest import mock

import discord

from classes.permissions_notice import DEFAULT_CHANNEL_PERMS, THREAD_CHANNEL_PERMS, default_channel_perms
from databases.transactions.ConfigData import ConfigData
from listeners.ThreadListeners import ThreadListeners, reopen_thread
from modules.Config import Config
from views.select.configselectroles import ConfigSelectChannels

GUILD_ID = 91
THREAD_ID = 500


def fake_thread(thread_id=THREAD_ID, archived=True, locked=False) :
	thread = mock.Mock(spec=discord.Thread)
	thread.id = thread_id
	thread.name = "age-log"
	thread.archived = archived
	thread.locked = locked
	thread.guild = mock.Mock(id=GUILD_ID)
	thread.guild.name = "Thread guild"
	thread.edit = mock.AsyncMock()
	return thread


class TestThreadsCanBeChosen(unittest.IsolatedAsyncioTestCase) :

	def test_config_channels_accepts_threads(self) :
		value = next(param for param in Config.channels.parameters if param.name == "value")
		self.assertIn(discord.ChannelType.text, value.channel_types)
		self.assertIn(discord.ChannelType.public_thread, value.channel_types)
		self.assertIn(discord.ChannelType.private_thread, value.channel_types)

	async def test_setup_select_accepts_threads(self) :
		select = next(item for item in ConfigSelectChannels().children if isinstance(item, discord.ui.ChannelSelect))
		self.assertEqual(select.channel_types, [discord.ChannelType.text, discord.ChannelType.public_thread,
		                                        discord.ChannelType.private_thread])


class TestThreadPermissions(unittest.TestCase) :

	def test_threads_need_send_messages_in_threads(self) :
		self.assertEqual(default_channel_perms(fake_thread()), THREAD_CHANNEL_PERMS)
		self.assertIn("send_messages_in_threads", THREAD_CHANNEL_PERMS)
		self.assertNotIn("send_messages", THREAD_CHANNEL_PERMS)

	def test_channels_need_send_messages(self) :
		self.assertEqual(default_channel_perms(mock.Mock(spec=discord.TextChannel)), DEFAULT_CHANNEL_PERMS)


class TestReopenConfigThreads(unittest.IsolatedAsyncioTestCase) :

	async def asyncSetUp(self) :
		self.config = ConfigData()
		self.config.conf[GUILD_ID] = {"AGE_LOG" : str(THREAD_ID)}
		# The cog starts its daily sweep; with no guilds that first run does nothing.
		self.cog = ThreadListeners(mock.Mock(guilds=[], wait_until_ready=mock.AsyncMock()))
		self.addCleanup(self.cog.cog_unload)

	def tearDown(self) :
		self.config.conf.pop(GUILD_ID, None)

	async def test_archived_config_thread_is_reopened(self) :
		after = fake_thread()
		await self.cog.on_thread_update(fake_thread(archived=False), after)
		after.edit.assert_awaited_once_with(archived=False)

	async def test_other_threads_are_left_alone(self) :
		after = fake_thread(thread_id=THREAD_ID + 1)
		await self.cog.on_thread_update(fake_thread(thread_id=THREAD_ID + 1, archived=False), after)
		after.edit.assert_not_awaited()

	async def test_locked_threads_stay_closed(self) :
		thread = fake_thread(locked=True)
		await reopen_thread(thread)
		thread.edit.assert_not_awaited()

	async def test_failed_reopen_does_not_raise(self) :
		thread = fake_thread()
		thread.edit.side_effect = discord.Forbidden(mock.Mock(status=403, reason="Forbidden"), "Missing Access")
		await reopen_thread(thread)

	async def test_sweep_reopens_threads_archived_while_offline(self) :
		thread = fake_thread()
		guild = mock.Mock(id=GUILD_ID)
		guild.get_channel_or_thread.return_value = None
		guild.fetch_channel = mock.AsyncMock(return_value=thread)
		self.cog.bot.guilds = [guild]
		with mock.patch("listeners.ThreadListeners.asyncio.sleep", mock.AsyncMock()) :
			await self.cog.reopen_config_threads.coro(self.cog)
		guild.fetch_channel.assert_awaited_once_with(THREAD_ID)
		thread.edit.assert_awaited_once_with(archived=False)
