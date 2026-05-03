import logging
import traceback

import discord
from discord_py_utilities.messages import send_message, send_response

from classes.lobbytimers import LobbyTimers
from databases.transactions.AgeRoleTransactions import AgeRoleTransactions
from databases.transactions.ConfigData import ConfigData
from resources.data.IDVerificationMessage import create_message
from resources.data.config_variables import VERIFICATION_KEY, VerificationMethods
from views.buttons.idsubmitbutton import IdSubmitButton
from views.modals.verifyModal import VerifyModal


class TOSButton(discord.ui.View) :
	def __init__(self, guild_id, reverify=False) :
		super().__init__(timeout=None)
		self.reverify = reverify

		# Logging for debugging
		logging.info(f"TOSButton: {reverify}")
		stack = traceback.format_stack()
		caller = stack[-2] if len(stack) > 1 else "Unknown"
		logging.info(f"TOSButton created with reverify={reverify}. Created by: {caller}")

		suffix = "_reverify" if reverify else "_standard"

		if ConfigData().get_key(guild_id, VERIFICATION_KEY, VerificationMethods.BASIC) in [VerificationMethods.BASIC, VerificationMethods.ALL] or reverify:
			self.add_basic_verification(suffix)
		if ConfigData().get_key(guild_id, VERIFICATION_KEY, VerificationMethods.BASIC) in [VerificationMethods.IDVERIFY, VerificationMethods.ALL] and not reverify:
			self.add_id_verification(suffix)
		self.add_decline_verification(suffix)


	async def check_cooldown_and_respond(self, interaction: discord.Interaction) -> bool :
		"""Helper to handle boilerplate cooldown logic."""
		cooldown = LobbyTimers().check_cooldown(interaction.guild.id, interaction.user.id)
		if cooldown :
			await send_response(
				interaction,
				f"{interaction.user.mention} You are on cooldown for verification. Please wait {discord.utils.format_dt(cooldown, style='R')} before trying again.",
				ephemeral=True
			)
			return True
		return False

	async def disable_buttons(self, interaction: discord.Interaction, msg: str = None) :
		"""Disables all buttons and updates the message."""
		for item in self.children :
			if isinstance(item, discord.ui.Button) :
				item.disabled = True
		if msg:
			await interaction.edit_original_response(content=msg, view=self)
			return
		await interaction.edit_original_response(view=self)

	# --- Callbacks ---

	async def american_callback(self, interaction: discord.Interaction) :
		if await self.check_cooldown_and_respond(interaction) :
			return
		await interaction.response.send_modal(VerifyModal(month=1, day=2, year=3, reverify=self.reverify))
		await self.disable_buttons(interaction)

	async def european_callback(self, interaction: discord.Interaction) :
		if await self.check_cooldown_and_respond(interaction) :
			return
		await interaction.response.send_modal(VerifyModal(day=1, month=2, year=3, reverify=self.reverify))
		await self.disable_buttons(interaction)

	async def universal_callback(self, interaction: discord.Interaction) :
		if await self.check_cooldown_and_respond(interaction) :
			return
		await interaction.response.send_modal(VerifyModal(day=3, month=2, year=1, reverify=self.reverify))
		await self.disable_buttons(interaction)

	async def decline_callback(self, interaction: discord.Interaction) :
		mod_channel_id = ConfigData().get_key_int(interaction.guild.id, "approval_channel")
		modlobby = interaction.guild.get_channel(mod_channel_id)

		if modlobby :
			await send_message(
				modlobby,
				f"{interaction.user.mention} has declined the privacy policy and the verification process has been stopped."
			)

		await send_response(
			interaction,
			"Privacy policy declined and the staff team has been informed. You can click the 'dismiss message' to hide it."
		)
		await self.disable_buttons(interaction)


	async def id_callback(self, interaction: discord.Interaction) :
		if await self.check_cooldown_and_respond(interaction) :
			return
		await interaction.response.defer(ephemeral=True)
		embed = discord.Embed(title="ID Verification", description=create_message(interaction,
		                                                                          min_age=AgeRoleTransactions().get_minimum_age(
			                                                                          interaction.guild.id), user_init=True))
		embed.set_footer(text=f"{interaction.guild.id}")
		await self.disable_buttons(interaction, f"A direct message has been sent with instructions")
		await send_message(interaction.user, embed=embed, view=IdSubmitButton(user_initiated=True))


	def add_basic_verification(self, suffix):
		self.btn_american = discord.ui.Button(
			label="I accept the privacy policy (MM/DD/YYYY)",
			style=discord.ButtonStyle.green,
			custom_id=f"usa_accept{suffix}",
			row=0
		)
		self.btn_european = discord.ui.Button(
			label="I accept the privacy policy (DD/MM/YYYY)",
			style=discord.ButtonStyle.green,
			custom_id=f"eu_accept{suffix}",
			row=1
		)
		self.btn_universal = discord.ui.Button(
			label="I accept the privacy policy (YYYY/MM/DD)",
			style=discord.ButtonStyle.green,
			custom_id=f"universal_accept{suffix}",
			row=2
		)


		# 2. Assign Callbacks
		self.btn_american.callback = self.american_callback
		self.btn_european.callback = self.european_callback
		self.btn_universal.callback = self.universal_callback

		# 3. Add Items to View
		self.add_item(self.btn_american)
		self.add_item(self.btn_european)
		self.add_item(self.btn_universal)

	def add_id_verification(self, suffix):
		self.id_button = discord.ui.Button(
			label="I accept the privacy policy (ID Verification)",
			style=discord.ButtonStyle.green,
			custom_id=f"ID_accept{suffix}",
			row=3
		)
		self.id_button.callback = self.id_callback
		self.add_item(self.id_button)

	def add_decline_verification(self, suffix):
		self.btn_decline = discord.ui.Button(
			label="I decline the privacy policy",
			style=discord.ButtonStyle.danger,
			custom_id=f"decline{suffix}",
			row=4
		)
		self.btn_decline.callback = self.decline_callback


		self.add_item(self.btn_decline)
