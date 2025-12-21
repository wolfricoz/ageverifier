import logging

import discord
from discord_py_utilities.messages import send_response

from classes.retired.discord_tools import send_message
from databases.controllers.VerificationTransactions import VerificationTransactions
from views.modals.inputmodal import InputModal, send_modal


#
class IdReviewButton(discord.ui.View) :
	def __init__(self) :
		super().__init__(timeout=None)
		self.member: discord.Member = None

	@discord.ui.button(label="Review ID", style=discord.ButtonStyle.blurple, custom_id="id_review")
	async def idverify(self, interaction: discord.Interaction, button: discord.ui.Button) :
		if not await self.load_data(interaction) :
			return await send_response(interaction, "Could not load user data from message!", ephemeral=True)
		if not interaction.user.guild_permissions.administrator :
			return await send_response(interaction, "You must have the administrator permission to execute this action!",
			                           ephemeral=True)
		idcheck = VerificationTransactions().get_id_info(self.member.id)
		if not idcheck :
			return await send_response(interaction, f"No ID verification request found for <@{self.member.id}>",
			                           ephemeral=True)
		if not idcheck.idmessage :
			return await send_response(interaction,
			                           f"ID verification message expired for <@{self.member.id}>, we hold these up to 7 days.",
			                           ephemeral=True)

		# fetch the image from DMs
		message = await self.member.dm_channel.fetch_message(idcheck.idmessage)
		await send_response(interaction, f"Here is the ID verification request for <@{self.member.id}>\n"
		                                 f"{message.attachments[0].url}", ephemeral=True)

	@discord.ui.button(label="Confirm Date of Birth", style=discord.ButtonStyle.green, custom_id="confirm_dob")
	async def idconfirm(self, interaction: discord.Interaction, button: discord.ui.Button) :
		if not interaction.user.guild_permissions.administrator :
			return await send_response(interaction, "You must have the administrator permission to execute this action!",
			                           ephemeral=True)
		user = interaction.message.mentions[-1]
		from views.modals.idverify import IdVerifyModal

		await interaction.response.send_modal(IdVerifyModal(user, interaction.message))
		return None

	@discord.ui.button(label="Decline ID", style=discord.ButtonStyle.red, custom_id="decline_id")
	async def decline(self, interaction: discord.Interaction, button: discord.ui.Button) :
		if not interaction.user.guild_permissions.administrator :
			return await send_response(interaction, "You must have the administrator permission to execute this action!",
			                           ephemeral=True)
		if not await self.load_data(interaction) :
			return await send_response(interaction, "Could not load user data from message!", ephemeral=True)

		await send_modal(interaction, title="Decline ID Verification",
		                 confirmation=f"Thank you for providing a reason for declining the ID verification for <@{self.member.id}>.")
		idcheck = VerificationTransactions().get_id_info(self.member.id)

		await send_response(interaction,
		                    f"Declined ID verification for: <@{self.member.id}> by {interaction.user.mention}", )
		if idcheck.idmessage :
			try :
				from classes.idcheck import IdCheck
				await IdCheck.remove_idmessage(self.member, idcheck)

			except (discord.NotFound, discord.Forbidden) as e :
				logging.info(f"Could not delete previous ID message for {self.member.id}: {e}")
		await send_message(self.member,
		                   "Your ID verification has been declined by the server staff with the following reason:\n")
		await interaction.message.delete()
		return None

	async def load_data(self, interaction: discord.Interaction) -> bool :
		if len(interaction.message.embeds) < 1 :
			return False
		self.member = interaction.guild.get_member(int(interaction.message.embeds[0].footer.text))
		if not self.member :
			try :
				self.member = await interaction.guild.fetch_member(int(interaction.message.embeds[0].footer.text))
			except Exception :
				return False
		return True
