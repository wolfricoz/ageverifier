import discord

from classes.AgeCalculations import AgeCalculations
from classes.databaseController import ConfigData, UserTransactions, VerificationTransactions
from classes.encryption import Encryption
from classes.support.discord_tools import send_message, send_response
from classes.whitelist import check_whitelist
from modules.config import config
from views.buttons.approvalbuttons import ApprovalButtons
from views.modals.verifyModal import VerifyModal


class TOSButton(discord.ui.View) :
	def __init__(self) :
		super().__init__(timeout=None)

	@discord.ui.button(label="I accept the privacy policy (MM/DD/YYYY)",
	                   style=discord.ButtonStyle.green,
	                   custom_id="usa_accept",
	                   row=1)
	async def american(self, interaction: discord.Interaction, button: discord.ui.Button) :
		await interaction.response.send_modal(VerifyModal())

	@discord.ui.button(label="I accept the privacy policy (DD/MM/YYYY)",
	                   style=discord.ButtonStyle.green,
	                   custom_id="eu_accept",
	                   row=2)
	async def european(self, interaction: discord.Interaction, button: discord.ui.Button) :
		await interaction.response.send_modal(VerifyModal(day=2, month=3))

	@discord.ui.button(label="I accept the privacy policy (YYYY/MM/DD)",
	                   style=discord.ButtonStyle.green,
	                   custom_id="universal_accept",
	                   row=3)
	async def universal(self, interaction: discord.Interaction, button: discord.ui.Button) :
		await interaction.response.send_modal(VerifyModal(day=4, month=3, year=2))

	@discord.ui.button(label="I decline the privacy policy",
	                   style=discord.ButtonStyle.danger,
	                   custom_id="decline",
	                   row=4)
	async def button(self, interaction: discord.Interaction, button: discord.ui.Button) :
		modlobby = interaction.guild.get_channel(ConfigData().get_key_int(interaction.guild.id, 'lobbymod'))
		if modlobby is None :
			return

		await send_message(modlobby,
		                   f"{interaction.user.mention} has declined the privacy policy and the verification process has been stopped.")
		await send_response(interaction,
		                    "Privacy policy declined and the staff team has been informed. You can click the 'dismiss message' to hide it.")
