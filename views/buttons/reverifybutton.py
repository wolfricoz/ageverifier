import logging

import discord
from discord_py_utilities.messages import send_response

from classes.AgeCalculations import AgeCalculations
from classes.encryption import Encryption
from classes.helpers import fetch_member
from classes.lobbyprocess import LobbyProcess
from classes.lobbytimers import LobbyTimers
from databases.transactions.ConfigData import ConfigData
from databases.transactions.UserTransactions import UserTransactions
from databases.transactions.VerificationTransactions import VerificationTransactions
from views.buttons.approvalbuttons import ApprovalButtons
from views.buttons.tosbutton import TOSButton


class ReVerifyButton(discord.ui.View) :
	def __init__(self) :
		super().__init__(timeout=None)

	@discord.ui.button(label="Start ReVerification here!", style=discord.ButtonStyle.green,
	                   custom_id="reverification_role")
	async def verify(self, interaction: discord.Interaction, button: discord.ui.Button) :
		if cooldown := LobbyTimers().check_cooldown(interaction.guild.id, interaction.user.id) :
			await send_response(interaction,
			                    f"{interaction.user.mention} You are on cooldown for verification. Please wait {discord.utils.format_dt(cooldown, style='R')} before trying again.",
			                    ephemeral=True)
			return

		idcheck = await self.id_verified_check(interaction, True)
		if idcheck :
			return
		# if AccessControl().is_premium(interaction.guild.id) and ConfigData().get_toggle(interaction.guild.id, "ONLINE_VERIFICATION") :
		#
		# 	uuid = WebsiteDataTransactions().create(user_id=interaction.user.id, guild_id=interaction.guild.id)
		# 	website_base = os.getenv("DASHBOARD_URL")
		# 	url = f"{website_base}/ageverifier/verification/{interaction.guild.id}/{uuid}"
		#
		# 	await send_response(interaction, f"This server uses our online verification system. Please use the button below to visit our verification page.", ephemeral=True, view=WebsiteButton(url))
		# 	return


		await send_response(interaction,
		                    f"{interaction.user.mention} To verify using AgeVerifier, you must accept our [Privacy Policy](https://wolfricoz.github.io/ageverifier/privacypolicy.html). By accepting, you consent to your date of birth being stored for verification purposes. Please review the policy and if you accept our privacy policy, please click 'I accept.'",
		                    view=TOSButton(reverify=True), ephemeral=True)

	def get_user_data(self, user_id: int) :
		user = UserTransactions().get_user(user_id)
		dob = Encryption().decrypt(user.date_of_birth)
		age = AgeCalculations.dob_to_age(dob)
		return dob, age

	async def id_verified_check(self, interaction: discord.Interaction, reverify= False) -> bool :
		try :
			modlobby = interaction.guild.get_channel(
				ConfigData().get_key_int_or_zero(interaction.guild.id, "approval_channel"))
			if modlobby is None :
				await send_response(interaction, f"Lobbymod not set, inform the server staff to setup the server.",
				                    ephemeral=True)
				logging.info(f"{interaction.guild.name} does not have lobbymod set.")
				return False
			# User is ID verified, so the user does not need to input their dob and age again.
			userinfo = VerificationTransactions().get_id_info(interaction.user.id)
			if userinfo is None :
				return False
			member = await fetch_member(interaction.guild, interaction.user.id)
			if member is None :
				return False

			if userinfo.idverified :
				logging.info("user is id verified")
				dob, age = self.get_user_data(interaction.user.id)
				message = f'Due to prior ID verification, you do not need to re-enter your date of birth and age. You will be granted access once the staff completes the verification process.'
				LobbyTimers().add_cooldown(interaction.guild.id, interaction.user.id,
				                           ConfigData().get_key_int_or_zero(interaction.guild.id, 'COOLDOWN'))
				automatic_status = ConfigData().get_key_or_none(interaction.guild.id, "automatic_verification")
				if automatic_status and automatic_status == "enabled".upper() or reverify:
					await LobbyProcess.approve_user(interaction.guild, interaction.user, dob, age, "automatic_verification",
					                                reverify=reverify)
					await send_response(interaction,
					                    f'Thank you for submitting your age and dob! You will be let through immediately!',
					                    ephemeral=True)
					return True
				mod_lobby = ConfigData().get_key_int(interaction.guild.id, "approval_channel")
				mod_channel = interaction.guild.get_channel(mod_lobby)

				# Ensure we are working with a Member object, this reduces issues with guild-specific actions
				approval_buttons = ApprovalButtons(age=age, dob=dob, user=member)
				await send_response(interaction, message,
				                    ephemeral=True)
				await approval_buttons.send_message(interaction.guild, interaction.user , mod_channel, id_verified=True, )

				return True
			return False
		except Exception as e :
			logging.error(e, exc_info=True)
			return False
