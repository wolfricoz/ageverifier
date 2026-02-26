import discord
from discord_py_utilities.messages import await_message, send_message, send_response

from databases.transactions.ConfigData import ConfigData
from databases.transactions.VerificationTransactions import VerificationTransactions
from views.buttons.idreviewbuttons import IdReviewButton


#
class IdSubmitButton(discord.ui.View) :
	def __init__(self) :
		super().__init__(timeout=None)
		self.guild = None

	custom_id = "id_submit_buttons"




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
			await send_response(interaction, "Too many attachments attached to this message, please send only 1 image.")
		mod_channel: discord.TextChannel = self.guild.get_channel(
			ConfigData().get_key_int_or_zero(self.guild.id, "verification_failure_log"))
		if mod_channel is None:
			await send_response(interaction, "Lobbymod channel not set, please contact the server staff.", ephemeral=True)
			return
		message = await send_message(
			interaction.user,
			"Thank you — we received your ID for verification. Attached is a private copy of what you submitted.\n\n"
			"This message is the only storage location for your submission. We keep it on Discord for review only, for up to 7 days. "
			"When the review is complete, or 7 days pass (whichever comes first), this message will be deleted and no other copies will be kept.",
			files=[await attachment.to_file() for attachment in message.attachments]
		)
		idcheck = VerificationTransactions().get_id_info(interaction.user.id)
		if idcheck and idcheck.idmessage:
			from classes.idcheck import IdCheck
			await IdCheck.remove_idmessage(interaction.user, idcheck)
		VerificationTransactions().update_verification(interaction.user.id, idmessage=message.id)
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
		embed.set_footer(text=interaction.user.id)
		await mod_channel.send(f"{interaction.user.mention} has submitted an ID for verification.", embed=embed, view=IdReviewButton())
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
		self.guild = interaction.client.get_guild(int(interaction.message.embeds[0].footer.text))
		if not self.guild :
			try:
				self.guild = await interaction.client.fetch_guild(int(interaction.message.embeds[0].footer.text))
			except Exception:
				return False
		return True