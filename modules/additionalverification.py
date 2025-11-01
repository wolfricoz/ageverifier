import discord
from discord.ext import commands
from discord.ext.commands import GroupCog
from discord import app_commands

from classes.access import AccessControl


class AdditionalVerification(GroupCog, name="reverify"):

	def __init__(self, bot):
		self.bot = bot


def setup(bot: commands.Bot):
	bot.add_cog(AdditionalVerification(bot))

	@app_commands.command(name="create")
	@AccessControl().check_premium()
	async def create(interaction: discord.Interaction, button_text: str = "Start Verification", desc_text: str = ""):
		"""Creates the button to start the secondary verification"""
		pass


	