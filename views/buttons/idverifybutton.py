import discord

from classes.databaseController import VerificationTransactions
from classes.support.discord_tools import send_response
from views.modals.idverify import IdVerifyModal


class IdVerifyButton(discord.ui.View) :
	def __init__(self) :
		super().__init__(timeout=None)

	@discord.ui.button(label="Confirm ID Verify", style=discord.ButtonStyle.green, custom_id="id_verify")
	async def idverify(self, interaction: discord.Interaction, button: discord.ui.Button) :
		if not interaction.user.guild_permissions.administrator :
			return await send_response(interaction, "You must have the administrator permission to execute this action!", ephemeral=True)
		user = interaction.message.mentions[0]
		await interaction.response.send_modal(IdVerifyModal(user, interaction.message))

	@discord.ui.button(label="Remove ID Check", style=discord.ButtonStyle.red, custom_id="remove")
	async def remove(self, interaction: discord.Interaction, button: discord.ui.Button) :
		if not interaction.user.guild_permissions.administrator :
			return await send_response(interaction, "You must have the administrator permission to execute this action!", ephemeral=True)
		user = interaction.message.mentions[0]
		if VerificationTransactions.set_idcheck_to_false(user.id) is False :
			await send_response(interaction,f"Can't find entry: <@{user.id}>")
			return
		await send_response(interaction, f"Deleted entry: <@{user.id}>")
		await interaction.message.delete()

	@discord.ui.button(label="User Left", style=discord.ButtonStyle.red, custom_id="left")
	async def remove(self, interaction: discord.Interaction, button: discord.ui.Button) :
		if not interaction.user.guild_permissions.administrator :
			return await send_response(interaction, "You must have the administrator permission to execute this action!", ephemeral=True)
		await interaction.message.delete()
