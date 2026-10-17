import asyncio
import logging

import discord
from discord.ext import tasks
from discord.ext.commands import Bot, Cog

from databases.transactions.ConfigData import ConfigData
from resources.data.config_variables import channelchoices


def is_config_thread(thread: discord.Thread) -> bool :
	"""Whether the thread is one of the guild's /config channels."""
	return any(ConfigData().get_channel_id(thread.guild.id, key) == thread.id for key in channelchoices)


async def reopen_thread(thread: discord.Thread) -> None :
	"""Unarchives a config thread. Locked threads were closed by staff on purpose, so those stay closed."""
	if not thread.archived or thread.locked :
		return
	try :
		await thread.edit(archived=False)
		logging.info(f"Reopened config thread {thread.name} ({thread.id}) in {thread.guild.name}")
	except discord.HTTPException as e :
		logging.info(f"Could not reopen config thread {thread.id} in {thread.guild.name}: {e}")


# discord.py drops archived threads from its cache, so every guild.get_channel_or_thread() lookup of an
# archived config thread returns None and the bot treats the channel as not set. Keeping them open avoids that.
class ThreadListeners(Cog) :

	def __init__(self, bot: Bot) :
		self.bot = bot
		self.reopen_config_threads.start()

	def cog_unload(self) :
		self.reopen_config_threads.cancel()

	@Cog.listener("on_thread_update")
	async def on_thread_update(self, before: discord.Thread, after: discord.Thread) -> None :
		if after.archived and not before.archived and is_config_thread(after) :
			await reopen_thread(after)

	@tasks.loop(hours=24)
	async def reopen_config_threads(self) -> None :
		"""Catches config threads that were archived while the bot was offline."""
		for guild in self.bot.guilds :
			for key in channelchoices :
				channel_id = ConfigData().get_channel_id(guild.id, key)
				if channel_id is None or guild.get_channel_or_thread(channel_id) is not None :
					continue
				try :
					channel = await guild.fetch_channel(channel_id)
				except discord.HTTPException :
					continue
				if isinstance(channel, discord.Thread) :
					await reopen_thread(channel)
				await asyncio.sleep(1)

	@reopen_config_threads.before_loop
	async def before_reopen_config_threads(self) -> None :
		await self.bot.wait_until_ready()


async def setup(bot: Bot) :
	await bot.add_cog(
		ThreadListeners(bot),
	)
