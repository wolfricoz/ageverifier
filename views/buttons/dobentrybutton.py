"""This module is for the confirm buttons, which are used to confirm or cancel an action."""
import re

import discord

from databases.controllers.UserTransactions import UserTransactions
from classes.encryption import Encryption


class dobentry(discord.ui.View):
    """This class is for the confirm buttons, which are used to confirm or cancel an action."""

    def __init__(self):
        super().__init__(timeout=None)



    @discord.ui.button(label="Get Info", style=discord.ButtonStyle.primary, custom_id="get_dob")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        """get info from message thhe button is attached to"""
        match = re.search(r'UID: (\d+)', interaction.message.content)
        user = UserTransactions().get_user(match.group(1))
        await interaction.response.send_message(f"Date of birth: {Encryption().decrypt(user.date_of_birth)}", ephemeral=True)



