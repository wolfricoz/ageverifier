"""Allows users to text(str) data into the database through discord.ui.Modal"""
import discord
from discord_py_utilities.messages import send_response

from databases.controllers.ConfigTransactions import ConfigTransactions


class ConfigInputUnique(discord.ui.Modal, title='set config message'):

    def __init__(self, key):
        super().__init__(timeout=None)  # Set a timeout for the modal
        self.key = key
    text = discord.ui.TextInput(
            label='What is the message?',
            style=discord.TextStyle.long,
            placeholder='Type the message here',
            max_length=512
    )

    async def on_submit(self, interaction: discord.Interaction):
        ConfigTransactions().config_unique_add(guildid=interaction.guild.id, key=self.key, value=self.text.value, overwrite=True)

        await send_response(interaction, f"{self.key} has been added to the database with value:\n{self.text.value}", ephemeral=True)

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        print(error)
        await send_response(interaction, 'Oops! Something went wrong.', ephemeral=True)


class ConfigInput(discord.ui.Modal, title='set config message'):
    custom_id = ""

    def __init__(self, key):
        super().__init__(timeout=None)
        self.key = key

    text = discord.ui.TextInput(
            label='What is the message?',
            style=discord.TextStyle.long,
            placeholder='Type your waning here...',
            max_length=1024,
    )

    async def on_submit(self, interaction: discord.Interaction):
        result = ConfigTransactions().config_unique_add(guildid=interaction.guild.id, key=self.key.upper(),
                                                      value=self.text.value, overwrite=False)
        if result is False:
            await send_response(interaction, f"{self.key} already exists", ephemeral=True)
            return

        await send_response(interaction, f"{self.key} has been added to the database with value:\n{self.text.value}", ephemeral=True)

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        print(error)
        await send_response(interaction, 'Oops! Something went wrong.', ephemeral=True)
