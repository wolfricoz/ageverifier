import logging
import os
import time

import discord
from discord import app_commands
from discord.ext import commands, tasks
from discord_py_utilities.messages import send_response

from classes.support.queue import Queue

STUCK_AFTER = 300


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
        self.watchdog.start()

    @app_commands.command(name="restart_queue", description="[dev command] Restart the bot queue")
    @check_access()
    async def restart_queue(self, interaction: discord.Interaction, empty: bool = False) :
        if empty :
            Queue().clear()
        Queue().task_finished = True
        Queue().task_started_at = None
        # restart() only works while the loop is still alive; once its task has finished it
        # does nothing, which is the case this command is most often reached for.
        if self.queue.is_running():
            self.queue.restart()
        else:
            self.queue.start()
        await send_response(interaction, f"Queue restarted. Empty: {empty}", ephemeral=True)

    def cog_unload(self):
        self.queue.cancel()
        self.display_status.cancel()
        self.watchdog.cancel()

    @tasks.loop(seconds=0.3)
    async def queue(self):
        try:
            await Queue().start()
        except Exception as e:
            logging.error(e, exc_info=True)

    @tasks.loop(seconds=3)
    async def display_status(self):
        # The presence update talks to the gateway and throws on a closing/reconnecting
        # connection (ClientConnectionResetError). Unhandled, that stops this loop for the
        # rest of the process' life, so it never gets to leave the try.
        try:
            status = "Keeping the community safe!"
            if not Queue().empty():
                self.status_changed = True
                status = Queue().status()

            if self.status_changed:
                await self.bot.change_presence(activity=discord.CustomActivity(name=status, emoji='🖥️'))
                if Queue().empty():
                    self.status_changed = False
        except Exception as e:
            logging.warning(f"Could not update the queue status presence: {e}")

    @tasks.loop(seconds=30)
    async def watchdog(self):
        """Revives the queue if it stopped or wedged.

        A dead queue is silent: verifications keep being accepted and simply never get
        their roles, log entry or welcome, because everything after approve_user runs
        through the queue. Loop.restart() is deliberately not used - it is a no-op once
        the internal task has already finished, which is exactly the case we recover from.
        """
        try:
            queue = Queue()
            started_at = queue.task_started_at
            if started_at is not None and time.monotonic() - started_at > STUCK_AFTER:
                logging.error(
                    f"Queue task has been running for over {STUCK_AFTER}s; releasing the queue.")
                queue.task_finished = True
                queue.task_started_at = None
            if not self.queue.is_running():
                logging.error("Queue loop is not running, restarting it.")
                queue.task_finished = True
                queue.task_started_at = None
                self.queue.start()
            if not self.display_status.is_running():
                logging.warning("Status loop is not running, restarting it.")
                self.display_status.start()
        except Exception as e:
            logging.error(f"Queue watchdog failed: {e}", exc_info=True)


    @queue.error
    async def queue_error(self, exception: BaseException):
        logging.error("Queue loop stopped unexpectedly; the watchdog will restart it.",
                      exc_info=exception)

    @display_status.error
    async def display_status_error(self, exception: BaseException):
        logging.error("Status loop stopped unexpectedly; the watchdog will restart it.",
                      exc_info=exception)

    @watchdog.error
    async def watchdog_error(self, exception: BaseException):
        logging.error("Queue watchdog stopped unexpectedly.", exc_info=exception)

    @queue.before_loop
    async def before_queue(self):
        await self.bot.wait_until_ready()

    @display_status.before_loop
    async def before_display(self):
        await self.bot.wait_until_ready()

    @watchdog.before_loop
    async def before_watchdog(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(queueTask(bot))
