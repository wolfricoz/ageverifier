import logging

import discord

from classes.AgeCalculations import AgeCalculations
from classes.databaseController import ConfigData, UserTransactions, VerificationTransactions
from classes.encryption import Encryption
from classes.support.discord_tools import send_message, send_response
from classes.whitelist import check_whitelist
from views.buttons.approvalbuttons import ApprovalButtons
from views.buttons.tosbutton import TOSButton
from views.modals.verifyModal import VerifyModal


class VerifyButton(discord.ui.View) :
	def __init__(self) :
		super().__init__(timeout=None)

	@discord.ui.button(label="Start Verification here!", style=discord.ButtonStyle.green, custom_id="verify")
	async def verify(self, interaction: discord.Interaction, button: discord.ui.Button) :
		idcheck = await self.id_verified_check(interaction)
		print(idcheck)
		if idcheck :
			return
		await send_response(interaction,
		                    f"{interaction.user.mention} To verify using AgeVerifier, you must accept our [Privacy Policy](https://wolfricoz.github.io/ageverifier/privacypolicy.html). By accepting, you consent to your date of birth being stored for verification purposes. Please review the policy and if you accept our privacy policy, please click 'I consent.'",
		                    view=TOSButton(), ephemeral=True)

	def get_user_data(self, user_id: int) :
		user = UserTransactions.get_user(user_id)
		dob = Encryption().decrypt(user.date_of_birth)
		age = AgeCalculations.dob_to_age(dob)
		return dob, age

	async def id_verified_check(self, interaction: discord.Interaction) -> bool :
		try:
			modlobby = interaction.guild.get_channel(ConfigData().get_key_int(interaction.guild.id, 'lobbymod'))
			if modlobby is None :
				logging.info(f"{interaction.guild.name} does not have lobbymod set.")
				return False
			# User is ID verified, so the user does not need to input their dob and age again.
			userinfo = VerificationTransactions.get_id_info(interaction.user.id)
			if userinfo is None:
				return False
			if userinfo.idverified is True :
				print("user is id verified")
				dob, age = self.get_user_data(interaction.user.id)
				message = f'Due to prior ID verification, you do not need to re-enter your date of birth and age. You will be granted access once the staff completes the verification process.'
				if check_whitelist(interaction.guild.id) :
					await send_message(modlobby,
					                   f"\n{interaction.user.mention} is ID verified with: {dob}. You can let them through with the buttons below."
					                   f"\n-# [LOBBY DEBUG] To manually process: `?approve {interaction.user.mention} {age} {dob}`",
					                   view=ApprovalButtons(age=age, dob=dob, user=interaction.user))
					await send_response(interaction, message,
					                    ephemeral=True)
					return True
				await send_message(modlobby,
				                   f"\n{interaction.user.mention} is ID verified. You can let them through with the buttons below."
				                   f"\n-# [LOBBY DEBUG] Server not whitelisted: Personal Information (PI) hidden",
				                   view=ApprovalButtons(age=age, dob=dob, user=interaction.user))
				await send_response(interaction, message,
				                    ephemeral=True)
				return True
			return False
		except Exception as e:
			logging.error(e, exc_info=True)
			return False
