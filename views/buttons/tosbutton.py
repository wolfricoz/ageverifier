import discord

from classes.databaseController import ConfigData
from classes.support.discord_tools import send_message, send_response
from modules.config import config
from views.modals.verifyModal import VerifyModal


class TOSButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="I accept the privacy policy", style=discord.ButtonStyle.green, custom_id="accept")
    async def test(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(VerifyModal())

    @discord.ui.button(label="I decline the privacy policy", style=discord.ButtonStyle.danger, custom_id="decline")
    async def button(self, interaction: discord.Interaction, button: discord.ui.Button):
        modlobby = interaction.guild.get_channel(ConfigData().get_key_int(interaction.guild.id, 'lobbymod'))
        if modlobby is None:
            return
        await send_message(modlobby, f"{interaction.user.mention} has declined the privacy policy and the verification process has been stopped.")
        await send_response(interaction, "Privacy policy declined and the staff team has been informed. You can click the 'dismiss message' to hide it.")
