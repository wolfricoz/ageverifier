import logging

import discord
from discord.ext import commands, tasks

from classes.support.queue import Queue


class queueTask(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.queue.start()
        self.display_status.start()

    def cog_unload(self):
        self.queue.cancel()

    @tasks.loop(seconds=0.3)
    async def queue(self):
        try:
            await Queue().start()
        except Exception as e:
            logging.error(e, exc_info=True)

    @tasks.loop(seconds=3)
    async def display_status(self):
        await self.bot.wait_until_ready()
        status = "Keeping the community safe!"
        if not Queue().empty():
            status = Queue().status()

        await self.bot.change_presence(activity=discord.CustomActivity(name=status, emoji='🖥️'))

    @queue.before_loop
    async def before_queue(self):
        await self.bot.wait_until_ready()

    @queue.before_loop
    async def before_display(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(queueTask(bot))
