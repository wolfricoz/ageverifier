import logging

import discord
from discord import app_commands
from discord.ext import commands, tasks
from discord_py_utilities.messages import send_response

from classes.support.queue import Queue


def check_access() :
	def pred(interaction: discord.Interaction) -> bool :
		if interaction.user.id == int(os.getenv('DEVELOPER')) :
			return True
		return False

	return app_commands.check(pred)


class queueTask(commands.Cog):
    status_changed = False

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.queue.start()
        self.display_status.start()

    @app_commands.command(name="restart_queue", description="[dev command] Restart the bot queue")
    @check_access()
    async def restart_queue(self, interaction: discord.Interaction, empty: bool = False) :
        if empty :
            Queue().clear()
        Queue().task_finished = True
        self.queue.restart()
        await send_response(interaction, f"Queue restarted. Empty: {empty}", ephemeral=True)

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
            self.status_changed = True
            status = Queue().status()

        if self.status_changed:
            await self.bot.change_presence(activity=discord.CustomActivity(name=status, emoji='🖥️'))
            if Queue().empty():
                self.status_changed = False

    @queue.before_loop
    async def before_queue(self):
        await self.bot.wait_until_ready()

    @queue.before_loop
    async def before_display(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(queueTask(bot))
