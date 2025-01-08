"""this module handles the lobby."""
import os

import discord
from discord import app_commands
from discord.ext import commands

from classes.databaseController import VerificationTransactions
from classes.support.discord_tools import send_message, send_response
from classes.support.queue import queue
from views.buttons.agebuttons import AgeButtons
from views.buttons.dobentrybutton import dobentry
from views.buttons.verifybutton import VerifyButton


class idcheck(commands.GroupCog) :
	def __init__(self, bot: commands.Bot) :
		self.bot = bot
		self.index = 0
		self.bot.add_view(VerifyButton())
		self.bot.add_view(AgeButtons())
		self.bot.add_view(dobentry())

	@app_commands.command()
	@app_commands.checks.has_permissions(manage_messages=True)
	async def get(self, interaction: discord.Interaction,
	              user: discord.User) :
		"""[manage_messages] Get the ID check status of the specified user"""
		await send_response(interaction, f"⌛ checking if {user.mention} is on the ID list", ephemeral=True)
		user = VerificationTransactions.get_id_info(user.id)
		if user is None :
			await interaction.followup.send("Not found")
			return
		data = {
			"user"        : user.uid,
			"Reason"      : user.reason,
			"idcheck"     : user.idcheck,
			"idverifier"  : user.idverified,
			"verifieddob" : user.verifieddob
		}

		embed = discord.Embed(title="USER INFO",
		                      description="Reminder: This data is only allowed to be shared with relevant parties.")
		for title, value in data.items() :
			embed.add_field(name=title, value=value, inline=False)
		await send_response(interaction, f"", embed=embed, ephemeral=True)

	@app_commands.command()
	@app_commands.checks.has_permissions(administrator=True)
	async def update(self, interaction: discord.Interaction, idcheck: bool,
	                 user: discord.User, reason: str = None) :
		"""[administrator] Update the id check status and reason of the specified user."""
		await send_response(interaction, f"⌛ updating {user.mention}'s ID check entry'", ephemeral=True)

		if reason is None :
			await interaction.followup.send(f"Please include a reason")
			return
		VerificationTransactions.update_check(user.id, reason, idcheck)
		await interaction.followup.send(
			f"{user.mention}'s userid entry has been updated with reason: {reason} and idcheck: {idcheck}")

	@app_commands.command()
	@app_commands.checks.has_permissions(administrator=True)
	async def delete(self, interaction: discord.Interaction,
	                 user: discord.User) :
		"""[Administrator] Delete the ID check entry of a specified user."""
		await send_response(interaction, f"⌛ deleting {user.mention}'s ID check entry'", ephemeral=True)
		dev_channel = interaction.client.get_channel(int(os.getenv('DEV')))
		if VerificationTransactions.set_idcheck_to_false(user.id) is False :
			await interaction.followup.send(f"Can't find entry: <@{user.id}>")
			return
		await interaction.followup.send(f"Deleted entry: <@{user.id}>")
		queue().add(send_message(dev_channel,
		                         f"{interaction.user.name} in {interaction.guild.name} removed id check for {user.global_name}"),
		            0)

	@app_commands.command()
	@app_commands.checks.has_permissions(manage_messages=True)
	async def create(self, interaction: discord.Interaction, user: discord.User,
	                 reason: str = None) :
		"""[manage_messages] Adds specified user to the ID list"""
		await send_response(interaction, f"⌛ creating {user.mention}'s ID check entry'", ephemeral=True)
		if reason is None :
			await interaction.followup.send(f"Please include a reason")
			return
		VerificationTransactions.add_idcheck(user.id, reason, True)
		await interaction.followup.send(
			f"<@{user.id}>'s userid entry has been added with reason: {reason} and idcheck: {True}")


async def setup(bot) :
	"""Adds the cog to the bot."""
	await bot.add_cog(idcheck(bot))
