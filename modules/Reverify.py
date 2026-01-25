import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import GroupCog
from discord_py_utilities.messages import send_message, send_response

from classes.access import AccessControl
from views.buttons.reverifybutton import ReVerifyButton


class Reverify(GroupCog, name="reverify", description="Commands for setting up and managing the reverification process.") :
	"""
	<h3>Premium Feature: Reverify</h3>

	Reverification is the process of asking existing members to verify themselves again to gain access to certain channels or roles. This is often used in servers with NSFW content or other restricted areas to ensure that members still meet the requirements for access. By using reverification, server admins can maintain a safe and compliant environment for their members, while also providing an additional layer of security against potential rule violations. This uses the same verification system as the initial verification process, except it only adds one role upon successful verification and is always automatic.

	Configurations needed to use reverification:
	- reverification_role
	- all of the verification configs

	"""

	def __init__(self, bot) :
		self.bot = bot

	@app_commands.command(name="create")
	@AccessControl().check_premium()
	async def create(self, interaction: discord.Interaction, channel: discord.TextChannel, desc_text: str = " ") :
		"""
		Creates the button to start the secondary verification

		This command creates a button in the specified channel that users can click to start the secondary verification process, which assigns them the reverification role upon successful verification.

		**Permissions:**
		- You need to have the `Manage Guild` permission to use this command.
		- Premium access is required to use this feature.

		"""
		await send_response(interaction, f"creating reverification button in {channel.name}", ephemeral=True)
		view = ReVerifyButton()
		await send_message(channel, desc_text, view=view)


async def setup(bot: commands.Bot) :
	await bot.add_cog(Reverify(bot))
