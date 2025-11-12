import discord

from classes.access import AccessControl
from classes.retired.discord_tools import send_message
from databases.controllers.AgeRoleTransactions import AgeRoleTransactions
from databases.controllers.VerificationTransactions import VerificationTransactions
from discord_py_utilities.messages import send_response

from resources.data.IDVerificationMessage import create_message
from views.buttons.idsubmitbutton import IdSubmitButton
from views.modals.idverify import IdVerifyModal

#
class IdVerifyButton(discord.ui.View) :
	def __init__(self) :
		super().__init__(timeout=None)

	@discord.ui.button(label="Request ID", style=discord.ButtonStyle.blurple, custom_id="id_request")
	async def idverify(self, interaction: discord.Interaction, button: discord.ui.Button) :
		if not interaction.user.guild_permissions.administrator :
			return await send_response(interaction, "You must have the administrator permission to execute this action!", ephemeral=True)
		if not AccessControl().is_premium(interaction.guild.id):
			return await send_response(interaction, "This feature is only for premium servers, please reach out to the user and then use the confirm ID verify button.", ephemeral=True)
		user = interaction.message.mentions[-1]
		idcheck = VerificationTransactions().get_id_info(user.id)
		if not idcheck :
			return await send_response(interaction, f"No ID verification request found for <@{user.id}>", ephemeral=True)

		try:
			embed = discord.Embed(title="ID Verification", description=create_message(interaction, min_age=AgeRoleTransactions().get_minimum_age(interaction.guild.id)))
			embed.set_footer(text=f"{interaction.guild.id}")
			embed.add_field(name="ID Check", value=idcheck.reason, inline=False)

			await send_message(user, embed=embed, view=IdSubmitButton())
			await send_response(interaction, "Successfully sent ID verification request.!", ephemeral=True)
		except discord.Forbidden or discord.NotFound:
			await send_response(interaction, "Could not DM user.", ephemeral=True)
		except Exception as e :
			await send_response(interaction, f"Could not DM user due to an error: {e}", ephemeral=True)

		return None

	@discord.ui.button(label="Confirm ID Verify", style=discord.ButtonStyle.green, custom_id="id_verify")
	async def idconfirm(self, interaction: discord.Interaction, button: discord.ui.Button) :
		if not interaction.user.guild_permissions.administrator :
			return await send_response(interaction, "You must have the administrator permission to execute this action!", ephemeral=True)
		user = interaction.message.mentions[-1]
		await interaction.response.send_modal(IdVerifyModal(user, interaction.message))
		return None

	@discord.ui.button(label="Remove ID Check", style=discord.ButtonStyle.red, custom_id="remove")
	async def remove(self, interaction: discord.Interaction, button: discord.ui.Button) :
		if not interaction.user.guild_permissions.administrator :
			return await send_response(interaction, "You must have the administrator permission to execute this action!", ephemeral=True)
		user = interaction.message.mentions[-1]
		if VerificationTransactions().set_idcheck_to_false(user.id, server=interaction.guild.name) is False :
			await send_response(interaction,f"Can't find entry: <@{user.id}>")
			return None
		await send_response(interaction, f"Deleted entry: <@{user.id}>")
		await interaction.message.delete()
		return None

	@discord.ui.button(label="User Left", style=discord.ButtonStyle.red, custom_id="left")
	async def left(self, interaction: discord.Interaction, button: discord.ui.Button) :
		if not interaction.user.guild_permissions.administrator :
			return await send_response(interaction, "You must have the administrator permission to execute this action!", ephemeral=True)
		await interaction.message.delete()
		return None
