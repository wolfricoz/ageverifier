import logging

import discord
from discord_py_utilities.messages import send_message, send_response

from classes.support.queue import Queue
from databases.exceptions.KeyNotFound import KeyNotFound
from databases.transactions.ConfigData import ConfigData
from databases.transactions.UserTransactions import UserTransactions


class GDPRRemoval(discord.ui.View) :
	def __init__(self) :
		super().__init__(timeout=None)

	@discord.ui.button(label="I want my data removed", style=discord.ButtonStyle.danger, custom_id="remove")
	async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button) :
		await send_response(interaction, "Thank you, your data will be hidden now.")
		UserTransactions().soft_delete(interaction.user.id, "Deleted By User (GDPR)")
		embed = discord.Embed(
			title=f"{interaction.user.global_name} has requested data removal!",
			description="This user has requested that all their data be removed from the bot. As a result, we can no longer guarantee their age. The bot will automatically remove the entry from your lobby log channel."
		)
		embed.add_field(
			name="What should I do?",
			value="We strongly recommend returning the member to the lobby using `/lobby returnlobby` or removing them from your server."
		)
		embed.set_footer(text="GDPR Right to Erasure Request")
		for guild in interaction.client.guilds:
			await self.delete_lobby_entry(interaction, guild)
			if interaction.user in guild.members:
				try:
					mod_lobby = guild.get_channel(ConfigData().get_key_int(guild.id, "approval_channel"))
					await send_message(mod_lobby, embed=embed)
				except KeyNotFound:
					pass
				except discord.Forbidden:
					await send_message(interaction.guild.owner, embed=embed)


	async def delete_lobby_entry(self, interaction: discord.Interaction, guild: discord.Guild):
		try:
			lobby_age: discord.TextChannel = guild.get_channel(ConfigData().get_key_int(guild.id, "age_log"))
			async for message in lobby_age.history(limit=None):
				if str(interaction.user.id) in message.content:
					logging.info(f"[GDPR] Deleting LobbyLog message in {guild.name}")
					Queue().add(message.delete())
		except KeyNotFound:
			print(f"could not delete entries in {guild.name} because lobbylog not setup")

