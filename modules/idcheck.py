import os

import discord
from discord import app_commands
from discord.ext import commands
from discord_py_utilities.messages import send_message, send_response

from classes.access import AccessControl
from classes.encryption import Encryption
from classes.idcheck import IdCheck
from classes.support.queue import Queue
from databases.current import IdVerification
from databases.transactions.VerificationTransactions import VerificationTransactions
from resources.data.responses import StringStorage
from views.buttons.confirm import Confirm
from views.modals.inputmodal import send_modal


class idcheck(commands.GroupCog, description="Commands for managing manual ID verification requests.") :
	"""
	Commands for managing manual ID verification requests.
	These tools are for server staff to flag users who require a manual ID check and to manage that status.
	Access to these commands is restricted.
	"""
	def __init__(self, bot: commands.Bot) :
		self.bot = bot
		self.index = 0


	@app_commands.command(description="Retrieves the ID check status for a specific user.")
	@app_commands.checks.has_permissions(manage_messages=True)
	async def get(self, interaction: discord.Interaction,
	              user: discord.User) :
		"""
        Retrieves the ID check status for a specific user.
        This command will show you if a user is flagged for a manual ID check, the reason for it, and if they have been verified.
        The information is sensitive and will be shown to you privately.

        **Permissions:**
        - You'll need the `Manage Messages` permission to use this command.
        """
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

	@app_commands.command(description="Updates a user's ID check status.")
	@app_commands.checks.has_permissions(administrator=True)
	async def update(self, interaction: discord.Interaction, idcheck: bool,
	                 user: discord.User, reason: str = None) :
		"""
        Updates a user's ID check status.
        You can use this to manually flag a user for an ID check or to clear their flag after they've been verified.
        A reason is required to keep a log of why the status was changed.

        **Permissions:**
        - You'll need the `Administrator` permission to use this command.
        """
		await send_response(interaction, f"⌛ updating {user.mention}'s ID check entry'", ephemeral=True)

		if reason is None :
			await interaction.followup.send(f"Please include a reason")
			return
		VerificationTransactions().update_check(user.id, reason, idcheck, server=interaction.guild.name)
		await interaction.followup.send(
			f"{user.mention}'s userid entry has been updated with reason: {reason} and idcheck: {idcheck}")

	@app_commands.command(description="Removes a user's ID check entry from the database.")
	@app_commands.checks.has_permissions(administrator=True)
	async def delete(self, interaction: discord.Interaction,
	                 user: discord.User) :
		"""
        Removes a user's ID check entry from the database.
        This effectively clears their ID check flag. This action is logged for security purposes.

        **Permissions:**
        - You'll need the `Administrator` permission to use this command.
        """
		await send_response(interaction, f"⌛ deleting {user.mention}'s ID check entry'", ephemeral=True)
		dev_channel = interaction.client.get_channel(int(os.getenv('DEV')))
		if VerificationTransactions().set_idcheck_to_false(user.id, server=interaction.guild.name) is False :
			await interaction.followup.send(f"Can't find entry: <@{user.id}>")
			return
		await interaction.followup.send(f"Deleted entry: <@{user.id}>")
		Queue().add(send_message(dev_channel,
		                         f"{interaction.user.name} in {interaction.guild.name} removed id check for {user.global_name}"),
		            0)

	@app_commands.command(description="Flags a user and adds them to the manual ID check list.")
	@app_commands.checks.has_permissions(manage_messages=True)
	async def create(self, interaction: discord.Interaction, user: discord.User,
	                 reason: str = None) :
		"""
        Flags a user and adds them to the manual ID check list.
        This is the first step in requiring a user to provide manual identification. You must provide a reason for this action.
        If the user is already on the list, you'll be asked if you want to update their entry.

        **Permissions:**
        - You'll need the `Manage Messages` permission to use this command.
        """
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

	@app_commands.command(description="Sends a direct message to a user requesting they provide their ID.")
	@app_commands.checks.has_permissions(manage_messages=True)
	async def send(self, interaction: discord.Interaction, user: discord.Member) :
		"""
        Sends a direct message to a user requesting they provide their ID for verification.
        This command will first ask you for a reason, which will be included in the message to the user.
        This is a premium feature.

        **Permissions:**
        - You'll need the `Manage Messages` permission.
        - This is a Premium-only command.
        """
		if not AccessControl().is_premium(interaction.guild.id):
			return await send_response(interaction, "This feature is only for premium servers, please reach out to the user and verify manually.", ephemeral=True)
		reason = await send_modal(interaction, f"Adding reason to the ID check for {user.name}", "ID Check Request")
		if reason is None :
			return None
		id_check: IdVerification = VerificationTransactions().update_check(user.id, str(reason), True, server=interaction.guild.name)
		await IdCheck.send_id_log(interaction, user, reason)
		await IdCheck.send_id_check(interaction, user, id_check)
		return None


async def setup(bot) :
	"""Adds the cog to the bot."""
	await bot.add_cog(idcheck(bot))
