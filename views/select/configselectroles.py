import discord

from discord.ui import UserSelect
from discord.ui import ChannelSelect
# Only roles?
from discord.ui import RoleSelect
# Members and roles in one?
from discord.ui import MentionableSelect

# import for the decorator and callback...
from discord import ui, Interaction

# using...
# this example uses the UserSelect
class ConfigSelectChannels(ui.View):
    # @ui.select(cls=type_we_want, **other_things)
    @ui.select(cls=ChannelSelect, placeholder="Select a channel please!")
    async def my_user_select(self, interaction: Interaction, select: UserSelect):
        # handle the selected users here
        # select.values is a list of User or Member objects here
        # it will be a list of Role if you used RoleSelect
        # it will be a list of both Role and Member/User if you used MentionableSelect

        self.value = [user.id for user in select.values]
        await interaction.response.edit_message()
        self.stop()

    @ui.button(label="Cancel", style=discord.ButtonStyle.danger)
    async def cancel(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.value = None
        self.stop()

    # next
    @ui.button(label="Next", style=discord.ButtonStyle.primary)
    async def next(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.value = "next"
        self.stop()

class ConfigSelectRoles(ui.View):
    # @ui.select(cls=type_we_want, **other_things)
    @ui.select(cls=RoleSelect, placeholder="Select a channel please!")
    async def my_user_select(self, interaction: Interaction, select: UserSelect):
        # handle the selected users here
        # select.values is a list of User or Member objects here
        # it will be a list of Role if you used RoleSelect
        # it will be a list of both Role and Member/User if you used MentionableSelect

        self.value = [user.id for user in select.values]
        await interaction.response.edit_message()
        self.stop()

    @ui.button(label="Cancel", style=discord.ButtonStyle.danger)
    async def cancel(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.value = None
        self.stop()

    @ui.button(label="Next", style=discord.ButtonStyle.primary)
    async def next(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.value = "next"
        self.stop()
