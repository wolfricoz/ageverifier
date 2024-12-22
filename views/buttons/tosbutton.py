import discord

from classes.AgeCalculations import AgeCalculations
from classes.databaseController import ConfigData, UserTransactions, VerificationTransactions
from classes.encryption import Encryption
from classes.support.discord_tools import send_message, send_response
from classes.whitelist import check_whitelist
from modules.config import config
from views.buttons.agebuttons import AgeButtons
from views.modals.verifyModal import VerifyModal


class TOSButton(discord.ui.View) :
	def __init__(self) :
		super().__init__(timeout=None)

	@discord.ui.button(label="I accept the privacy policy", style=discord.ButtonStyle.green, custom_id="accept")
	async def test(self, interaction: discord.Interaction, button: discord.ui.Button) :
		await interaction.response.send_modal(VerifyModal())

	@discord.ui.button(label="I decline the privacy policy", style=discord.ButtonStyle.danger, custom_id="decline")
	async def button(self, interaction: discord.Interaction, button: discord.ui.Button) :
		modlobby = interaction.guild.get_channel(ConfigData().get_key_int(interaction.guild.id, 'lobbymod'))
		if modlobby is None :
			return

		# User is ID verified, so the user does not need to input their dob and age again.
		userinfo = VerificationTransactions.get_id_info(interaction.user.id)
		if userinfo.idcheck is True :
			dob, age = self.get_user_data(interaction.user.id)
			message = f'Due to prior ID verification, you do not need to re-enter your date of birth and age. You will be granted access once the staff completes the verification process.'
			if check_whitelist(interaction.guild.id) :
				await send_message(modlobby,
				                   f"\n{interaction.user.mention} is ID verified with: {dob}. You can let them through with the buttons below."
				                   f"\n-# [LOBBY DEBUG] To manually process: `?approve {interaction.user.mention} {age} {dob}`",
				                   view=AgeButtons(age=age, dob=dob, user=interaction.user))
				await send_response(interaction, message,
				                    ephemeral=True)
				return
			await send_message(modlobby,
			                   f"\n{interaction.user.mention} is ID verified. You can let them through with the buttons below."
			                   f"\n-# [LOBBY DEBUG] Server not whitelisted: Personal Information (PI) hidden",
			                   view=AgeButtons(age=age, dob=dob, user=interaction.user))
			await send_response(interaction, message,
			                    ephemeral=True)
			return

		await send_message(modlobby,
		                   f"{interaction.user.mention} has declined the privacy policy and the verification process has been stopped.")
		await send_response(interaction,
		                    "Privacy policy declined and the staff team has been informed. You can click the 'dismiss message' to hide it.")


	def get_user_data(self, user_id: int) :
		user = UserTransactions.get_user(user_id)
		dob = Encryption.decrypt(user.date_of_birth)
		_, age = AgeCalculations.agechecker(dob)
		return dob, age
