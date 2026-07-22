import logging

import discord
from discord_py_utilities.messages import await_message, send_message, send_response

from databases.transactions.ConfigData import ConfigData
from databases.transactions.VerificationTransactions import VerificationTransactions
from views.buttons.idreviewbuttons import IdReviewButton


#
class IdSubmitButton(discord.ui.View) :
	def __init__(self, user_initiated: bool = False, reverify = False) :
		super().__init__(timeout=None)
		self.guild = None
		self.user_initiated = user_initiated
		self.reverify = reverify

	custom_id = "id_submit_buttons"

	# Discord caps a bot's file uploads at 25 MB regardless of guild boost tier.
	DISCORD_BOT_UPLOAD_LIMIT = 25 * 1024 * 1024




	@discord.ui.button(label="Submit ID", style=discord.ButtonStyle.blurple, custom_id="id_answer")
	async def idverify(self, interaction: discord.Interaction, button: discord.ui.Button) :
		if not await self.load_data(interaction):
			await send_response(interaction, "Could not load guild data from message. Please contact the developer.", ephemeral=True)
			return
		if interaction.user not in self.guild.members:
			await send_response(interaction, "You are not a member of this server.", ephemeral=True)
			return
		try:
			message = await await_message(interaction, """ID verification reminder:
	* Black out everything on your ID except your date of birth (DOB). Make sure the DOB is clear and legible.
	* Include a handwritten note in the same image with your username, the text For ID verification, and the current date (YYYY-MM-DD).
	* Send the redacted ID image and the note together in one message.
	
	By providing your ID, you consent to ageverifier storing it for a maximum of 7 days.
	""")
		except TimeoutError:
			await send_response(interaction, "You did not respond in time. Please try again.", ephemeral=True)
			return
		if len(message.attachments) < 1:
			await send_response(interaction, "No attachments attached to this message")
			return
		if len(message.attachments) > 1:
			return await send_response(interaction, "Too many attachments attached to this message, please send only 1 image.")

		if self.user_initiated:
			mod_channel: discord.TextChannel = self.guild.get_channel(
				ConfigData().get_key_int_or_zero(self.guild.id, "approval_channel"))
		else:
			mod_channel: discord.TextChannel = self.guild.get_channel(
				ConfigData().get_key_int_or_zero(self.guild.id, "verification_failure_log"))
		if mod_channel is None:
			await send_response(interaction, "Lobbymod channel not set, please contact the server staff.", ephemeral=True)
			return
		attachment = message.attachments[0]
		if attachment.size > self.DISCORD_BOT_UPLOAD_LIMIT:
			await send_response(
				interaction,
				f"Your image is too large ({attachment.size / 1024 / 1024:.1f} MB). "
				f"The maximum accepted size is {self.DISCORD_BOT_UPLOAD_LIMIT // (1024 * 1024)} MB. "
				"Please compress or resize it and try again.",
				ephemeral=True,
			)
			return
		# Safety net for anything the size check can't predict: don't let a rejected upload
		# surface as an unhandled error.
		try:
			message = await send_message(
				interaction.user,
				"Thank you — we received your ID for verification. Attached is a private copy of what you submitted.\n\n"
				"This message is the only storage location for your submission. We keep it on Discord for review only, for up to 7 days. "
				"When the review is complete, or 7 days pass (whichever comes first), this message will be deleted and no other copies will be kept.",
				files=[await attachment.to_file()]
			)
		except discord.HTTPException as e:
			logging.error(f"Failed to store ID copy for {interaction.user.id} in {self.guild.name}: {e}", exc_info=True)
			await send_response(
				interaction,
				"We couldn't store your ID — Discord rejected the upload, most likely because the file is too large. "
				"Please try again with a smaller image, or contact server staff if this keeps happening.",
				ephemeral=True,
			)
			await send_message(mod_channel, f"[ID submit fail] Could not store an ID copy for {interaction.user.mention}; they were asked to retry with a smaller image.")
			return
		idcheck = VerificationTransactions().get_id_info(interaction.user.id)
		if idcheck and idcheck.idmessage:
			from classes.idcheck import IdCheck
			await IdCheck.remove_idmessage(interaction.user, idcheck)

		try:
			VerificationTransactions().add_idcheck(interaction.user.id, idcheck=False)
			VerificationTransactions().update_verification(interaction.user.id, idmessage=message.id)
		except Exception as e:
			logging.error(f"Failed to update ID record for {interaction.user.id} in {self.guild.name}: {e}", exc_info=True)
			await send_message(mod_channel, f"[ID record fail] Failed to update ID record, continuing verification.")
		embed = discord.Embed(
			title="ID Verification Submission",
			description=f"Submission from {interaction.user.mention}.",
			color=discord.Color.blue()
		)
		embed.add_field(
			name="Staff Notice",
			value="Do not share this ID outside of staff members responsible for verification or save this ID. Abuse will be grounds for immediate blacklisting.",
			inline=False
		)
		if self.reverify:
			embed.add_field(name="Reverify", value="true")
		embed.set_footer(text=interaction.user.id)
		await mod_channel.send(f"{interaction.user.mention} has submitted an ID for verification.", embed=embed, view=IdReviewButton(reverify=self.reverify))
		await send_response(interaction, "Your ID submission has been sent to the server staff for review. You will be notified once the review is complete.", ephemeral=True)
		await self.disable_buttons(interaction)

	@discord.ui.button(label="Decline ID Verification", style=discord.ButtonStyle.red, custom_id="id_decline")
	async def iddecline(self, interaction: discord.Interaction, button: discord.ui.Button):
		if not await self.load_data(interaction):
			await send_response(interaction, "Could not load guild data from message. Please contact the developer.", ephemeral=True)
			return
		if interaction.user not in self.guild.members:
			await send_response(interaction, "You are not a member of this server.", ephemeral=True)
			return
		await send_response(interaction, f"{interaction.user.mention} You have declined to submit ID verification. You will not be able to proceed with verification without submitting ID. If you change your mind, you can click the 'Submit ID' button again.", ephemeral=True)
		mod_channel = self.guild.get_channel(ConfigData().get_key_int_or_zero(self.guild.id, "approval_channel"))
		if mod_channel is None:
			await send_response(interaction, "Lobbymod channel not set, please contact the server staff.", ephemeral=True)
			return
		await mod_channel.send(f"{interaction.user.mention} ({interaction.user.id}) has declined to submit ID verification.")

	async def disable_buttons(self, interaction: discord.Interaction):
		for item in self.children:
			item.disabled = True
		try:
			await interaction.message.edit(view=self)
		except Exception:
			pass

	async def load_data(self, interaction: discord.Interaction) -> bool:
		if len(interaction.message.embeds) < 1:
			return False
		embed = interaction.message.embeds[0]

		if not embed.footer.text or not embed.footer.text.isnumeric():
			return False

		self.guild = interaction.client.get_guild(int(embed.footer.text))
		for field in embed.fields:
			if field.name == "Reverify":
				self.reverify = True

		if not self.guild :
			try:
				self.guild = await interaction.client.fetch_guild(int(embed.footer.text))
			except Exception:
				return False
		return True