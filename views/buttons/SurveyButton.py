import discord
from discord_py_utilities.messages import send_response

from views.modals.SurveyModal import SurveyModal


class SurveyButton(discord.ui.View) :
	def __init__(self, ) :
		self.guild: discord.Guild = None
		super().__init__(timeout=None)
		pass
	custom_id = "Survey_buttons"

	@discord.ui.button(label="Answer Survey", style=discord.ButtonStyle.green, custom_id="Asurvey")
	async def allow(self, interaction: discord.Interaction, button: discord.ui.Button) :
		"""This is a button"""
		if not await self.load_data(interaction) :
			return await send_response(interaction, "Could not load server data from message!", ephemeral=True)
		await interaction.response.send_modal(
			SurveyModal(interaction.client, "Server Feedback Survey", self.guild.id)
		)
		await self.disable_buttons(interaction)

	async def disable_buttons(self, interaction: discord.Interaction) :
		for item in self.children :
			item.disabled = True
		try :
			await interaction.message.edit(view=self)
		except Exception :
			pass

	async def load_data(self, interaction: discord.Interaction) :
		"""Load data from embed"""
		if len(interaction.message.embeds) < 1 :
			return False
		self.guild: discord.Guild = interaction.client.get_guild(interaction.message.embeds[0].footer.text)
		if not self.guild :
			self.guild = await interaction.client.fetch_guild(interaction.message.embeds[0].footer.text)
			if not self.guild :
				return False

		return True
