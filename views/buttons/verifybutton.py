import discord

from classes.support.discord_tools import send_response
from views.buttons.tosbutton import TOSButton
from views.modals.verifyModal import VerifyModal


class VerifyButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label=""
                             "ID Verify", style=discord.ButtonStyle.green, custom_id="id_verify")
    async def idverify(self, interaction: discord.Interaction, button: discord.ui.Button):
        raise NotImplementedError

    @discord.ui.button(label="Remove ID Check", style=discord.ButtonStyle.red, custom_id="remove")
    async def remove(self, interaction: discord.Interaction, button: discord.ui.Button):
        raise NotImplementedError
