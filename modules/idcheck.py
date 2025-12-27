import os

import discord
from discord import app_commands
from discord.ext import commands
from discord_py_utilities.messages import send_message, send_response

from classes.access import AccessControl
from classes.encryption import Encryption
from classes.idcheck import IdCheck
from classes.support.queue import Queue
from databases.transactions.VerificationTransactions import VerificationTransactions
from databases.current import IdVerification
from resources.data.responses import StringStorage
from views.buttons.confirm import Confirm
from views.modals.inputmodal import send_modal


class idcheck(commands.GroupCog) :
	def __init__(self, bot: commands.Bot) :
		self.bot = bot
		self.index = 0


	@app_commands.command()
	@app_commands.checks.has_permissions(manage_messages=True)
	async def get(self, interaction: discord.Interaction,
	              user: discord.User) :
		"""[manage_messages] Get the ID check status of the specified user"""
		await send_response(interaction, f"⌛ checking if {user.mention} is on the ID list", ephemeral=True)
		user = VerificationTransactions().get_id_info(user.id)
		if user is None :
			await interaction.followup.send("Not found")
			return
		data = {
			"user"        : user.uid,
			"Reason"      : user.reason,
			"idcheck"     : user.idcheck,
			"idverified"  : user.idverified,
			"verifieddob" : Encryption().decrypt(user.verifieddob) if user.verifieddob else ""
		}

		embed = discord.Embed(title="USER INFO",
		                      description="Reminder: This data is only allowed to be shared with relevant parties.")
		for title, value in data.items() :
			embed.add_field(name=title, value=value, inline=False)
		await send_response(interaction, StringStorage.NO_SHARE_REMINDER, embed=embed, ephemeral=True)

	@app_commands.command()
	@app_commands.checks.has_permissions(administrator=True)
	async def update(self, interaction: discord.Interaction, idcheck: bool,
	                 user: discord.User, reason: str = None) :
		"""[administrator] Update the id check status and reason of the specified user."""
		await send_response(interaction, f"⌛ updating {user.mention}'s ID check entry'", ephemeral=True)

		if reason is None :
			await interaction.followup.send(f"Please include a reason")
			return
		VerificationTransactions().update_check(user.id, reason, idcheck, server=interaction.guild.name)
		await interaction.followup.send(
			f"{user.mention}'s userid entry has been updated with reason: {reason} and idcheck: {idcheck}")

	@app_commands.command()
	@app_commands.checks.has_permissions(administrator=True)
	async def delete(self, interaction: discord.Interaction,
	                 user: discord.User) :
		"""[Administrator] Delete the ID check entry of a specified user."""
		await send_response(interaction, f"⌛ deleting {user.mention}'s ID check entry'", ephemeral=True)
		dev_channel = interaction.client.get_channel(int(os.getenv('DEV')))
		if VerificationTransactions().set_idcheck_to_false(user.id, server=interaction.guild.name) is False :
			await interaction.followup.send(f"Can't find entry: <@{user.id}>")
			return
		await interaction.followup.send(f"Deleted entry: <@{user.id}>")
		Queue().add(send_message(dev_channel,
		                         f"{interaction.user.name} in {interaction.guild.name} removed id check for {user.global_name}"),
		            0)

	@app_commands.command()
	@app_commands.checks.has_permissions(manage_messages=True)
	async def create(self, interaction: discord.Interaction, user: discord.User,
	                 reason: str = None) :
		"""[manage_messages] Adds specified user to the ID list"""
		await send_response(interaction, f"⌛ creating {user.mention}'s ID check entry'", ephemeral=True)
		if reason is None :
			await send_response(interaction, f"Please include a reason")
			return
		idinfo = VerificationTransactions().add_idcheck(user.id, reason, True, server=interaction.guild.name)
		if idinfo:
			if await Confirm().send_confirm(interaction, f"{user.name} is on the ID list already with reason: `{idinfo.reason}`, do you want to update it?") is False:
				return
			VerificationTransactions().update_check(user.id, reason, True, server=interaction.guild.name)
			await send_response(interaction, f"{user.mention}'s ID check entry has been updated with reason: {reason} and idcheck: {True}", ephemeral=True)
			return

		await send_response(interaction,
			f"<@{user.id}>'s userid entry has been added with reason: {reason} and idcheck: {True}")

	@app_commands.command()
	@app_commands.checks.has_permissions(manage_messages=True)
	async def send(self, interaction: discord.Interaction, user: discord.Member) :
		"""[manage_messages][premium] Sends an ID check request to the specified user."""
		if not AccessControl().is_premium(interaction.guild.id):
			return await send_response(interaction, "This feature is only for premium servers, please reach out to the user and verify manually.", ephemeral=True)
		reason = await send_modal(interaction, f"Adding reason to the ID check for {user.name}", "ID Check Request")
		if reason is None :
			return None
		id_check: IdVerification = VerificationTransactions().update_check(user.id, str(reason), True, server=interaction.guild.name)
		await IdCheck.send_id_check(interaction, user, id_check)
		return None


async def setup(bot) :
	"""Adds the cog to the bot."""
	await bot.add_cog(idcheck(bot))
