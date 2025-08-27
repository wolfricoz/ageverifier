"""Allowing and denying users based on age."""
import asyncio
import logging
import uuid
from datetime import datetime

import discord
from discord_py_utilities.messages import send_message, send_response

from classes.banwatch import BanWatch
from classes.encryption import Encryption
from classes.lobbyprocess import LobbyProcess
from classes.whitelist import check_whitelist
from databases.controllers.ButtonTransactions import LobbyDataTransactions
from databases.controllers.ConfigData import ConfigData
from databases.controllers.HistoryTransactions import JoinHistoryTransactions
from databases.controllers.VerificationTransactions import VerificationTransactions
from databases.enums.joinhistorystatus import JoinHistoryStatus
from views.modals.inputmodal import send_modal


class ApprovalButtons(discord.ui.View) :
	def __init__(self, age: int = None, dob: str = None, user: discord.Member = None) :
		self.age = age
		self.dob = dob
		self.user = user
		super().__init__(timeout=None)
		button = discord.ui.Button(label='Help', style=discord.ButtonStyle.url,
		                           url='https://wolfricoz.github.io/ageverifier/lobby.html', emoji="❓")
		self.add_item(button)

	async def send_message(self, interaction: discord.Interaction, mod_channel, id_verified=None) :
		# prepare the data
		message = f"\n{interaction.user.mention} has given {self.age} and dob matches. You can let them through with the buttons below."
		if check_whitelist(interaction.guild.id) :
			message = f"\n{interaction.user.mention} has given {self.age} {self.dob}. You can let them through with the buttons below."
		footer = f"{uuid.uuid4()}"
		previous_guilds = None
		# loading the config, to since some settings are used multiple times we do it here to prevent the same call being made multiple times
		legacy_message: bool = ConfigData().get_toggle(interaction.guild.id, "legacy_message", default="DISABLED")
		show_previous_servers: bool = ConfigData().get_toggle(interaction.guild.id, "show_previous_servers",
		                                                      default="ENABLED")
		show_bans: bool = ConfigData().get_toggle(interaction.guild.id, "bans", default="ENABLED")
		show_joined_at: bool = ConfigData().get_toggle(interaction.guild.id, "joined_at", default="ENABLED")
		show_created_at: bool = ConfigData().get_toggle(interaction.guild.id, "created_at", default="ENABLED")
		show_user_id: bool = ConfigData().get_toggle(interaction.guild.id, "user_id", default="ENABLED")
		picture_large: bool = ConfigData().get_toggle(interaction.guild.id, "picture_large", default="DISABLED")
		picture_small: bool = ConfigData().get_toggle(interaction.guild.id, "picture_small", default="ENABLED")
		show_inline: bool = ConfigData().get_toggle(interaction.guild.id, "show_inline", default="DISABLED")

		# fetching previous servers
		if show_previous_servers :
			previous_guilds = "\n".join([guild.get('name', 'Failed to fetch name') for guild in
			                             JoinHistoryTransactions().fetch_previous_verifications(interaction.user.id)])
		# filling the fields
		fields = {
			"ID Verified"            : id_verified,
			"Date of Birth"          : self.dob if check_whitelist(
				interaction.guild.id) and legacy_message is False else None,
			"Age"                    : self.age if legacy_message is False else None,
			"Banwatch Bans"          : await BanWatch().fetchBanCount(interaction.user.id) if show_bans else None, # Potentially premium?
			"Joined at"              : interaction.user.joined_at.strftime("%m/%d/%Y %I:%M %p") if show_joined_at else None,
			"Created at"             : interaction.user.created_at.strftime("%m/%d/%Y") if show_created_at else None,
			"Previous Verifications" : previous_guilds, # Potentially premium?
			"User ID"                : interaction.user.id if show_user_id else None,
		}
		profile_picture = interaction.user.avatar.url

		# Build the embed
		embed = discord.Embed(title=f"Date of Birth and Age submitted by: {interaction.user.name}", description=message if str(
			ConfigData().get_key(interaction.guild.id, "legacy_message",
			                     "DISABLED")).upper() == "ENABLED" else "You can modify this embed with `/config approval_toggles`",
		                      color=discord.Color.green())

		embed.set_footer(text=footer)
		try :
			if picture_large is True and picture_small is False :
				embed.set_image(url=profile_picture)
			if picture_small :
				embed.set_thumbnail(url=profile_picture)
		except :
			pass
		# Add the fields
		for key, value in fields.items() :
			if value is None :
				continue
			embed.add_field(name=key, value=value, inline=show_inline)
		# send the content and create the record
		msg = await send_message(mod_channel,
		                         f"{interaction.user.mention}\n-# All timestamps are (mm/dd/yyyy)",
		                         embed=embed,
		                         view=self)
		LobbyDataTransactions().create(footer, self.user.id, self.dob, self.age)

		await send_response(interaction,
		                    f'Thank you for submitting your age and dob! You will be let through soon!',
		                    ephemeral=True)

	@discord.ui.button(label="Approve User", style=discord.ButtonStyle.green, custom_id="allow")
	async def allow(self, interaction: discord.Interaction, button: discord.ui.Button) :
		"""starts approving process"""
		await self.disable_buttons(interaction, button)
		self.load_data(interaction)
		if self.age is None or self.dob is None or self.user is None :
			await send_response(interaction,
			                    'The bot has restarted and the data of this button is missing. Please use the command.',
			                    ephemeral=True)
			return
		logging.info(f"Interaction user: {getattr(interaction, 'user', None)}")
		logging.info(f"Interaction message: {getattr(interaction, 'message', None)}")
		logging.info(f"Interaction guild: {getattr(interaction, 'guild', None)}")
		logging.info(interaction)
		await send_response(interaction, "User approved.", ephemeral=True)
		# Share this with the age commands
		try :
			await LobbyProcess.approve_user(interaction.guild, self.user, self.dob, self.age, interaction.user.name)
		except discord.NotFound :
			await send_response(interaction, "User not found, please manually add them to the database.", ephemeral=True)

	@discord.ui.button(label="Flag for ID Check", style=discord.ButtonStyle.red, custom_id="ID")
	async def manual_id(self, interaction: discord.Interaction, button: discord.ui.Button) :
		"""Flags user for manual id."""
		await self.disable_buttons(interaction, button)
		self.load_data(interaction)
		reason = await send_modal(interaction, confirmation="The user has been flagged",
		                          title="Why should the user be ID Checked?", max_length=1500)
		if self.user is None :
			await interaction.followup.send(
				'The bot has restarted and the data of this button is missing. Please manually report user to admins',
				ephemeral=True)
		await interaction.followup.send('User flagged for manual ID.', ephemeral=True)
		idcheck = ConfigData().get_key_int(interaction.guild.id, "idlog")
		idlog = interaction.guild.get_channel(idcheck)
		VerificationTransactions().set_idcheck_to_true(self.user.id,
		                                               f"manually flagged by {interaction.user.name} with reason: {reason}",
		                                               server=interaction.guild.name)
		JoinHistoryTransactions().update(self.user.id, interaction.guild.id, JoinHistoryStatus.IDCHECK)
		await interaction.message.edit(view=self)
		await idlog.send(
			f"{interaction.user.mention} has flagged {self.user.mention} for manual ID with reason:\n"
			f"```{reason}```")

		return

	@discord.ui.button(label="NSFW Profile Warning", style=discord.ButtonStyle.danger, custom_id="NSFW")
	async def nsfw_warning(self, interaction: discord.Interaction, button: discord.ui.Button) :
		"""Flags user for nsfw warning."""
		await self.disable_buttons(interaction, button)
		self.load_data(interaction)
		if self.user is None :
			await interaction.followup.send(
				'The bot has restarted and the data of this button is missing. Please manually report user to admins',
				ephemeral=True)
		await interaction.followup.send('User flagged for NSFW Warning.', ephemeral=True)
		warning = f"""**NSFW Warning**\n
Hello, this is the moderation team for {interaction.guild.name}. As Discord TOS prohibits NSFW content anywhere that can be accessed without an age gate, we will have to ask that you inspect your profile and remove any NSFW content. This includes but is not limited to: 
* NSFW profile pictures 
* NSFW display names
* NSFW Biographies
* NSFW status messages
* NSFW Banners
* NSFW Pronouns
* and NSFW game activity. 

Once you've made these changes you may resubmit your age and date of birth. Thank you for your cooperation."""
		await self.user.send(warning)
		await self.disable_buttons(interaction, button)

		return

	@discord.ui.button(label="User Left (stores DOB)", style=discord.ButtonStyle.primary, custom_id="add")
	async def add_to_db(self, interaction: discord.Interaction, button: discord.ui.Button) :
		"""Adds user to db"""
		age_log = ConfigData().get_key_int(interaction.guild.id, "lobbylog")
		self.load_data(interaction)
		await self.disable_buttons(interaction, button, disable_add=True)
		if self.user is None :
			await interaction.followup.send(
				'The bot has restarted and the data of this button is missing. Please add the user manually.',
				ephemeral=True)
		await LobbyProcess.age_log(self.user.id, self.dob, interaction)
		await interaction.message.add_reaction("✅")
		await interaction.followup.send('User added to database and this message will be deleted in 3 minutes.',
		                                ephemeral=True)
		await asyncio.sleep(180)
		await interaction.message.delete()
		return

	async def disable_buttons(self, interaction, button: discord.ui.Button = None, update=True, disable_add=False) :
		"""disables buttons"""
		self.manual_id.disabled = True
		self.manual_id.style = discord.ButtonStyle.grey

		self.allow.disabled = True
		self.allow.style = discord.ButtonStyle.grey

		self.nsfw_warning.disabled = True
		self.nsfw_warning.style = discord.ButtonStyle.grey

		button.style = discord.ButtonStyle.green
		if disable_add :
			self.add_to_db.disabled = True
			self.add_to_db.style = discord.ButtonStyle.grey

		if update is False :
			return
		await interaction.response.edit_message(view=self)

	def load_data(self, interaction: discord.Interaction) :
		if len(interaction.message.embeds) < 1:
			return False

		embed = interaction.message.embeds[0]
		logging.info(embed.footer.text)
		data = LobbyDataTransactions().read(embed.footer.text)
		logging.info(data)
		self.user = interaction.guild.get_member(data.uid)
		self.dob = Encryption().decrypt(data.dob)
		self.age = data.age
		logging.info(self.age)
		logging.info(self.user)
		logging.info(self.dob)
		return True
