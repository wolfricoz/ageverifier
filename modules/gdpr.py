"""Checks the users invite info when they join and logs it"""
import os

import discord
from discord import app_commands
from discord.ext import commands

from classes.databaseController import UserTransactions, VerificationTransactions
from classes.support.discord_tools import send_message, send_response
from views.buttons.gdprremoval import GDPRRemoval


class gdpr(commands.GroupCog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="removal", description="Request removal of your data")
    async def removal(self, interaction: discord.Interaction):
        """Removes user data"""
        user = UserTransactions.get_user(interaction.user.id)
        if user is None or user.date_of_birth is None:
            await send_response(interaction, "No data found for you.")
            return
        dev_channel = self.bot.get_channel(int(os.getenv("DEV")))
        # await send_message(dev_channel, f"{interaction.user.mention} has requested to have their data removed, data has been marked for removal in 30 days.")
        text = """You have requested to have your data removed under GDPR. 

- AgeVerifier cannot confirm your age, so we will notify the owners of any guilds you are in.  
- Your data will be **hidden for 30 days** before being permanently deleted.  
- If you submit your date of birth again during this time, the removal process will be **canceled**.  

If you want to continue, please confirm your request."""


        await send_response(interaction, text, view=GDPRRemoval(), ephemeral=True)

    @app_commands.command(name="data", description="Request your data")
    async def data(self, interaction: discord.Interaction):
        """Returns user data"""
        dev = self.bot.get_user(188647277181665280)
        user_data = UserTransactions.get_user(interaction.user.id)
        id_verified = VerificationTransactions.get_id_info(interaction.user.id)
        if user_data is not None:
            await interaction.user.send(f"**__User Data Request__**"
                                        f"\nUser: {interaction.user.mention}({interaction.user.id})"
                                        f"No data found for you.")

        await interaction.user.send(f"**__User Data Request__**"
                                    f"\nUser: {interaction.user.mention}({interaction.user.id})"
                                    f"\ndate of birth: {user_data.date_of_birth if user_data.date_of_birth is not None else 'Not set'}"
                                    f"\nLast server: {user_data.server if user_data.server is not None else 'Not set'}"
                                    f"\nID Verification: {'Yes' if id_verified and id_verified.idverified else 'No'}"
                                    f"\n\nNote: All personal data is encrypted and stored securely. If you have any questions or concerns please contact the developer `ricostryker` or join our [support server](https://discord.gg/5tcpArff) and open a ticket.")

        await send_response(interaction, "Please contact the developer `ricostryker` to for help or join our [support server](https://discord.gg/5tcpArff) and open a ticket.", ephemeral=True)


async def setup(bot):
    """Adds cog to the bot"""
    await bot.add_cog(gdpr(bot))
