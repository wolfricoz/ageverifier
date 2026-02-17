import discord
from discord_py_utilities.messages import send_message, send_response

from classes.access import AccessControl
from classes.idcheck import IdCheck as IdCheckClass
from databases.transactions.VerificationTransactions import VerificationTransactions
from views.modals.idverify import IdVerifyModal


#
class IdVerifyButton(discord.ui.View) :
	def __init__(self) :
		super().__init__(timeout=None)
		self.user = None

	custom_id = "id_verify_buttons"

	@discord.ui.button(label="Request ID", style=discord.ButtonStyle.blurple, custom_id="id_request")
	async def idverify(self, interaction: discord.Interaction, button: discord.ui.Button) :
		if not interaction.user.guild_permissions.administrator :
			return await send_response(interaction, "You must have the administrator permission to execute this action!", ephemeral=True)
		if not await self.load_data(interaction) :
			return await send_response(interaction, "Could not load user data from message!", ephemeral=True)
		if not AccessControl().is_premium(interaction.guild.id):
			return await send_response(interaction, "This feature is only for premium servers, please reach out to the user and then use the confirm ID verify button.", ephemeral=True)

		idcheck = VerificationTransactions().get_id_info(self.user.id)
		if not idcheck :
			return await send_response(interaction, f"No ID verification request found for <@{self.user.id}>", ephemeral=True)

		await IdCheckClass.send_id_check(interaction, self.user, idcheck)
		await send_message(interaction.channel, f"{interaction.user.mention} sent a request to review the ID for <@{self.user.id}>.")



		return None

	@discord.ui.button(label="Confirm ID Verify", style=discord.ButtonStyle.green, custom_id="id_verify")
	async def idconfirm(self, interaction: discord.Interaction, button: discord.ui.Button) :
		if not interaction.user.guild_permissions.administrator :
			return await send_response(interaction, "You must have the administrator permission to execute this action!", ephemeral=True)
		if not await self.load_data(interaction) :
			return await send_response(interaction, "Could not load user data from message!", ephemeral=True)

		await interaction.response.send_modal(IdVerifyModal(self.user, interaction.message))
		return None

	@discord.ui.button(label="Remove ID Check", style=discord.ButtonStyle.red, custom_id="remove")
	async def remove(self, interaction: discord.Interaction, button: discord.ui.Button) :
		if not interaction.user.guild_permissions.administrator :
			return await send_response(interaction, "You must have the administrator permission to execute this action!", ephemeral=True)
		if not await self.load_data(interaction) :
			return await send_response(interaction, "Could not load user data from message!", ephemeral=True)

		if VerificationTransactions().set_idcheck_to_false(self.user.id, server=interaction.guild.name) is False :
			await send_response(interaction,f"Can't find entry: <@{self.user.id}>")
			return None
		await send_response(interaction, f"Deleted entry: <@{self.user.id}>")
		await interaction.message.delete()
		return None

	@discord.ui.button(label="User Left", style=discord.ButtonStyle.red, custom_id="left")
	async def left(self, interaction: discord.Interaction, button: discord.ui.Button) :
		if not interaction.user.guild_permissions.administrator :
			return await send_response(interaction, "You must have the administrator permission to execute this action!", ephemeral=True)
		await interaction.message.delete()
		return None


	async def load_data(self, interaction: discord.Interaction) -> bool:
		if len(interaction.message.embeds) < 1 :
			return False
		self.user = interaction.guild.get_member(int(interaction.message.embeds[0].footer.text))
		if self.user is None :
			return False
		return True