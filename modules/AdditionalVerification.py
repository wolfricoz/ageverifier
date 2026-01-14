import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import GroupCog
from discord_py_utilities.messages import send_message, send_response

from classes.access import AccessControl
from views.buttons.reverifybutton import ReVerifyButton


class AdditionalVerification(GroupCog, name="reverify") :

	def __init__(self, bot) :
		self.bot = bot

	@app_commands.command(name="create")
	@AccessControl().check_premium()
	async def create(self, interaction: discord.Interaction, channel: discord.TextChannel, desc_text: str = " ") :
		"""
		Creates the button to start the secondary verification

		This command creates a button in the specified channel that users can click to start the secondary verification process, this is often used to re-verify existing members to gain access to NSFW channels or other restricted areas. The role given upon successful verification is determined by the server's configuration.
		Configs:
		reverificationlog
		
		"""
		await send_response(interaction, f"creating reverification button in {channel.name}", ephemeral=True)
		view = ReVerifyButton()
		await send_message(channel, desc_text, view=view)


async def setup(bot: commands.Bot) :
	await bot.add_cog(AdditionalVerification(bot))
