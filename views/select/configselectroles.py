import discord
# import for the decorator and callback...
from discord import Interaction, ui
# Only roles?
from discord.ui import ChannelSelect, RoleSelect, UserSelect

from discord_py_utilities.messages import send_response


# Members and roles in one?


# using...
# this example uses the UserSelect
class ConfigSelectChannels(ui.View) :

	def __init__(self) :
		super().__init__(timeout=1800)
		self.value = None
		button = discord.ui.Button(label='Help', style=discord.ButtonStyle.url,
		                           url='https://wolfricoz.github.io/ageverifier/commands/Config.html', emoji="❓")
		self.add_item(button)

	# @ui.select(cls=type_we_want, **other_things)
	@ui.select(cls=ChannelSelect, channel_types=[discord.ChannelType.text], placeholder="Select a channel please!")
	async def my_channel_select(self, interaction: Interaction, select: UserSelect) :
		# handle the selected users here
		# select.values is a list of User or Member objects here
		# it will be a list of Role if you used RoleSelect
		# it will be a list of both Role and Member/User if you used MentionableSelect

		self.value = [channel.id for channel in select.values]
		if not self.value :
			return await send_response(interaction, "Please select a channel, not a category!", ephemeral=True)
		await interaction.response.edit_message()
		self.stop()

	@ui.button(label="Cancel", style=discord.ButtonStyle.danger)
	async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button) :
		self.value = None
		# Without a response Discord shows "This interaction failed" on every click.
		await interaction.response.edit_message()
		self.stop()

	# next
	@ui.button(label="Skip", style=discord.ButtonStyle.primary)
	async def next(self, interaction: discord.Interaction, button: discord.ui.Button) :
		self.value = "next"
		await interaction.response.edit_message()
		self.stop()


class ConfigSelectRoles(ui.View) :
	def __init__(self) :
		super().__init__(timeout=1800)
		self.value = None
		button = discord.ui.Button(label='Help', style=discord.ButtonStyle.url,
		                           url='https://wolfricoz.github.io/ageverifier/commands/Config.html', emoji="❓")
		self.add_item(button)

	# @ui.select(cls=type_we_want, **other_things)
	@ui.select(cls=RoleSelect, placeholder="Select a role please!")
	async def my_user_select(self, interaction: Interaction, select: UserSelect) :
		# handle the selected users here
		# select.values is a list of User or Member objects here
		# it will be a list of Role if you used RoleSelect
		# it will be a list of both Role and Member/User if you used MentionableSelect

		self.value = [user.id for user in select.values]
		await interaction.response.edit_message()
		self.stop()

	@ui.button(label="Cancel", style=discord.ButtonStyle.danger)
	async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button) :
		self.value = None
		# Without a response Discord shows "This interaction failed" on every click.
		await interaction.response.edit_message()
		self.stop()

	@ui.button(label="Skip", style=discord.ButtonStyle.primary)
	async def next(self, interaction: discord.Interaction, button: discord.ui.Button) :
		self.value = "next"
		await interaction.response.edit_message()
		self.stop()
