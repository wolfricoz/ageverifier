"""Config options for the bot."""
import datetime
import os
from datetime import timezone

from discord import app_commands
from discord.ext import commands
from discord_py_utilities.messages import send_message

import classes.whitelist as wl
from classes.access import AccessControl
from databases.transactions.ConfigData import ConfigData
from views.modals.inputmodal import send_modal
from views.select.configselectroles import *


class whitelist(commands.GroupCog, name="whitelist") :

	def __init__(self, bot: commands.Bot) :
		self.bot = bot

	@app_commands.command(name="add", description="[dev]Adds a guild to the whitelist")
	async def add(self, interaction: discord.Interaction, guild_id: str) :
		"""[DEV] Adds a guild to the whitelist"""
		if interaction.user.id != 188647277181665280 :
			await send_response(interaction, "You are not the developer", ephemeral=True)
			return
		wl.add_to_whitelist(guild_id)
		await send_response(interaction, f"{guild_id} has been added to the whitelist")

	@app_commands.command(name="remove", description="[dev]Removes a guild from the whitelist")
	async def remove(self, interaction: discord.Interaction, guild_id: str) :
		"""[DEV] Removes a guild from the whitelist"""
		if interaction.user.id != 188647277181665280 :
			await send_response(interaction, "You are not the developer", ephemeral=True)
			return
		wl.remove_from_whitelist(guild_id)
		await send_response(interaction, f"{guild_id} has been removed from the whitelist")

	@app_commands.command(name="apply", description="Apply to be whitelisted.")
	async def apply(self, interaction: discord.Interaction) :

		requirements = {
			'premium': AccessControl().is_premium(interaction.guild.id),
			'members': interaction.guild.member_count > 500,
			'guild_age' : interaction.guild.created_at.astimezone(timezone.utc) < (
						datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=180)),
			'owner': interaction.guild.owner.name,

		}
		embed = discord.Embed(title=f"{interaction.guild.name}'s whitelist request"

		)
		for r in requirements:
			embed.add_field(name=r, value=requirements[r], inline=False)
		if not all(requirements.values()) :
			await send_response(interaction, "You do not meet the criteria for whitelisting", embed=embed)
			return

		reason = await send_modal(interaction, "Thank you for submitting your reason")
		embed.description = reason.value

		await send_response(interaction, "Thank you for submitting your whitelisting application. The developer will reach out to you.\n\nPlease read this article to prepare for your inspection: https://wolfricoz.github.io/ageverifier/whitelisting.html", embed=embed)
		gid = os.getenv('SUPPORTGUILD')
		guild = self.bot.get_guild(gid)
		if not guild :
			guild = await self.bot.fetch_guild(gid)
		channel = ConfigData().get_channel(guild, "approval_channel")
		await send_message(channel, embed=embed)












async def setup(bot: commands.Bot) :
	"""Adds the cog to the bot"""
	await bot.add_cog(whitelist(bot))
