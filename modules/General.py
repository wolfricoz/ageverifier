import discord
from discord import app_commands
from discord.ext.commands import Bot, Cog

from classes.retired.discord_tools import send_response
from views.v2.HelpLayout import HelpLayout


class General(Cog) :

	def __init__(self, bot: Bot) :
		self.bot = bot

	@app_commands.command(name="help", description="Unsure of what a command does? Find it here!")
	async def help(self, interaction: discord.Interaction) :
		"""Provides information about the bot's commands and features."""

		help_text = (
			"**Bot Help Guide**\n\n"
			"To view the documentation of a command, please select it from the select menu below.\n\n"
		)
		helplayout = HelpLayout(help_text)

		await send_response(interaction, " ", view=helplayout, ephemeral=True)


async def setup(bot: Bot) :
	await bot.add_cog(
		General(bot),
	)
