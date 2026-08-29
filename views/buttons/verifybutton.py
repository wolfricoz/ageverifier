import logging
import os

import discord
from discord_py_utilities.messages import send_response

from classes.AgeCalculations import AgeCalculations
from classes.access import AccessControl
from classes.encryption import Encryption
from classes.gdpr import confirm_removal_cancellation
from classes.lobbyprocess import LobbyProcess
from classes.lobbytimers import LobbyTimers
from databases.transactions.ConfigData import ConfigData
from databases.transactions.UserTransactions import UserTransactions
from databases.transactions.VerificationTransactions import VerificationTransactions
from databases.transactions.WebsiteDataTransactions import WebsiteDataTransactions
from resources.data.config_variables import DEFAULT_VERIFICATION_BUTTON_LABEL, MAX_BUTTON_LABEL_LENGTH, \
	VERIFICATION_KEY, VerificationMethods
from views.buttons.approvalbuttons import ApprovalButtons
from views.buttons.tosbutton import TOSButton
from views.buttons.websitebutton import WebsiteButton


def get_verification_button_label(guild_id: int = None) -> str :
	"""Resolves the label on the verification button for a guild.

	A custom label is a premium perk, so non-premium guilds (and premium guilds that never
	set one) get DEFAULT_VERIFICATION_BUTTON_LABEL. The stored value is trimmed to Discord's
	button label limit; an over-long label would otherwise make the entire message fail to
	send, which would take the lobby down with it.
	"""
	# Test for guild ID, if not return default; this prevents errors.
	if not guild_id :
		return DEFAULT_VERIFICATION_BUTTON_LABEL
	if not AccessControl().is_premium(guild_id) :
		return DEFAULT_VERIFICATION_BUTTON_LABEL
	label = ConfigData().get_key_or_none(guild_id, "verification_button_label")
	if not label :
		return DEFAULT_VERIFICATION_BUTTON_LABEL
	# A button label is a single line: the dashboard's field is one line, but a value that
	# arrived any other way could contain newlines, which render badly on a button.
	label = " ".join(str(label).split())
	if not label :
		return DEFAULT_VERIFICATION_BUTTON_LABEL
	return label[:MAX_BUTTON_LABEL_LENGTH]


class VerifyButton(discord.ui.View) :
	def __init__(self, guild_id: int = None) :
		super().__init__(timeout=None)
		# guild_id is omitted by the persistent-view registrations in main.py/Lobby.py: those
		# only exist to route clicks on messages that were already sent, so the label they
		# carry is never displayed. It is passed whenever a new message is actually sent.
		if guild_id is not None :
			self.verify.label = get_verification_button_label(guild_id)

	@discord.ui.button(label="Start Age Verification!", style=discord.ButtonStyle.green, custom_id="verify")
	async def verify(self, interaction: discord.Interaction, button: discord.ui.Button) :
		if cooldown := LobbyTimers().check_cooldown(interaction.guild.id, interaction.user.id) :
			await send_response(interaction,
			                    f"{interaction.user.mention} You are on cooldown for verification. Please wait {discord.utils.format_dt(cooldown, style='R')} before trying again.",
			                    ephemeral=True)
			return

		# Before id_verified_check: that path can approve the user outright, which would clear a
		# pending removal without ever asking them.
		proceed, interaction = await confirm_removal_cancellation(interaction)
		if not proceed :
			return

		idcheck = await self.id_verified_check(interaction)
		if idcheck :
			return
		if AccessControl().is_premium(interaction.guild.id) and ConfigData().get_key(interaction.guild.id, VERIFICATION_KEY, VerificationMethods.BASIC) == VerificationMethods.WEBSITE :

			uuid = WebsiteDataTransactions().create(user_id=interaction.user.id, guild_id=interaction.guild.id)
			website_base = os.getenv("DASHBOARD_URL")
			url = f"{website_base}/ageverifier/verification/{interaction.user.id}/{interaction.guild.id}/{uuid}"

			await send_response(interaction, f"This server uses our online verification system. Please use the button below to visit our verification page.", ephemeral=True, view=WebsiteButton(url))
			return


		await send_response(interaction,
		                    f"{interaction.user.mention} To verify using AgeVerifier, you must accept our [Privacy Policy](https://wolfricoz.github.io/ageverifier/privacypolicy.html). By accepting, you consent to your date of birth being stored for verification purposes. Please review the policy and if you accept our privacy policy, please click 'I accept.'",
		                    view=TOSButton(interaction.guild_id), ephemeral=True)

	def get_user_data(self, user_id: int ):
		user = UserTransactions().get_user(user_id)
		dob = Encryption().decrypt(user.date_of_birth)
		age = AgeCalculations.dob_to_age(dob)
		return dob, age

	async def id_verified_check(self, interaction: discord.Interaction) -> bool :
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
			from classes.helpers import fetch_member
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
				if automatic_status and automatic_status == "enabled".upper() :
					await LobbyProcess.approve_user(interaction.guild, interaction.user, dob, age, "automatic_verification")
					await send_response(interaction,
					                    f'Thank you for submitting your age and dob! You will be let through immediately!',
					                    ephemeral=True)
					return True
				mod_lobby = ConfigData().get_key_int(interaction.guild.id, "approval_channel")
				mod_channel = interaction.guild.get_channel(mod_lobby)


				approval_buttons = ApprovalButtons(age=age, dob=dob, user=member)
				await send_response(interaction, message,
				                    ephemeral=True)
				await approval_buttons.send_message(interaction.guild, user=member , mod_channel=mod_channel, id_verified=True)

				return True
			return False
		except Exception as e :
			logging.error(e, exc_info=True)
			return False
