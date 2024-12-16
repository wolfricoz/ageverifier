import discord

from classes.support.discord_tools import send_response
from views.buttons.tosbutton import TOSButton
from views.modals.verifyModal import VerifyModal


class VerifyButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Start Verification here!", style=discord.ButtonStyle.green, custom_id="verify")
    async def test(self, interaction: discord.Interaction, button: discord.ui.Button):
        await send_response(interaction, f"{interaction.user.mention} To verify using AgeVerifier, you must accept our [Privacy Policy](https://wolfricoz.github.io/ageverifier/privacypolicy.html). By accepting, you consent to your date of birth being stored for verification purposes. Please review the policy and click 'Accept' to proceed.", view=TOSButton(), ephemeral=True)
