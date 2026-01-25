"""Creates a custom warning modal for the bot."""
import logging

import discord
from discord_py_utilities.messages import send_message, send_response

from databases.transactions.ConfigData import ConfigData


class SurveyModal(discord.ui.Modal) :
	custom_id = "InputModal"

	def __init__(self, bot, title, guild_id) :
		self.feedback = None
		self.like = None
		self.rating = None
		self.dislike = None
		self.guild: discord.Guild = bot.get_guild(guild_id)
		super().__init__(timeout=None, title=title)  # Set a timeout for the modal
		self.confirmation = f"Thank you for completing the survey for {self.guild.name}!"
		self.leave = discord.ui.TextInput(
			label='Why are you leaving the server?',
			style=discord.TextStyle.long,
			placeholder='Type your reason here...',
			max_length=1000,
			required=False
		)

		self.rating = discord.ui.TextInput(
			label='Rating (1-10)',
			style=discord.TextStyle.short,
			placeholder='Type your rating here... (1-10)',
			max_length=2  # Changed from 1 to allow "10"
		)
		self.like = discord.ui.TextInput(
			label='What did you like about the server?',
			style=discord.TextStyle.long,
			placeholder='type your likes here!',
			max_length=1000
		)
		self.dislike = discord.ui.TextInput(
			label='What did you dislike about the server?',
			style=discord.TextStyle.long,
			placeholder='Type your dislikes here!',
			max_length=1000
		)
		self.feedback = discord.ui.TextInput(
			label='Do you have any feedback?',
			style=discord.TextStyle.long,
			placeholder='Type your feedback here!',
			max_length=1000
		)
		self.contact = discord.ui.TextInput(
			label='May we contact you for further feedback? (yes/no)',
			style=discord.TextStyle.short,
			placeholder='Type yes or no',
			max_length=3
		)

		# Add all inputs to the modal
		self.add_item(self.rating)
		self.add_item(self.leave)
		self.add_item(self.like)
		self.add_item(self.dislike)
		self.add_item(self.feedback)
		self.add_item(self.contact)



	async def on_submit(self, interaction: discord.Interaction) -> None :
		try :
			modchannel = self.guild.get_channel(ConfigData().get_key_int_or_zero(self.guild.id, 'lobbymod'))
			if modchannel is None :
				return await self.send_message(interaction, "Could not find the mod channel to send the survey results to.")
			embed = discord.Embed(title=f"Survey from {interaction.user.name}", description=f"This survey is to help your server improve; please remain cordial with the user.", color=discord.Color.green())
			embed.add_field(name="Rating (1-10)", value=self.rating.value, inline=False)
			embed.add_field(name="leave reason", value=self.leave.value, inline=False)
			embed.add_field(name="Likes", value=self.like.value, inline=False)
			embed.add_field(name="Dislikes", value=self.dislike.value, inline=False)
			embed.add_field(name="Feedback", value=self.feedback.value, inline=False)
			embed.add_field(name="Contact Permission", value=self.contact.value, inline=False)
			embed.set_footer(text=f"User ID: {interaction.user.id} | Guild ID: {self.guild.id}")
			await send_message(modchannel, embed=embed)
			await self.send_message(interaction, self.confirmation)
		except discord.errors.HTTPException :
			pass


	async def on_error(self, interaction: discord.Interaction, error: Exception) -> None :
		print(error)
		await self.send_message(interaction, f"An error occurred: {error}")


	async def send_message(self, interaction: discord.Interaction, message: str) -> None :
		"""sends the message to the channel."""
		try :
			await send_response(interaction, message, ephemeral=True)
		except discord.errors.HTTPException :
			pass
		except Exception as e :
			logging.error(e)
