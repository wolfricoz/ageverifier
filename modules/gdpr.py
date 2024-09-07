"""Checks the users invite info when they join and logs it"""
from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands

from classes.databaseController import ConfigData, UserTransactions
from classes.helpers import has_onboarding, invite_info
from classes.support.discord_tools import send_response


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

        dev = self.bot.get_user(188647277181665280)
        await dev.send(f"User {interaction.user.mention}({interaction.user.id}) has requested data removal, please wait for them to contact.")
        await send_response(interaction, "Please contact the developer `ricostryker` to request data removal or join our [support server](https://discord.gg/5tcpArff) and open a ticket.", ephemeral=True)

    @app_commands.command(name="data", description="Request your data")
    async def data(self, interaction: discord.Interaction):
        """Returns user data"""
        dev = self.bot.get_user(188647277181665280)
        await dev.send(f"User {interaction.user.mention}({interaction.user.id}) has requested data, please wait for them to contact.")
        await send_response(interaction, "Please contact the developer `ricostryker` to request your data or join our [support server](https://discord.gg/5tcpArff) and open a ticket.", ephemeral=True)






async def setup(bot):
    """Adds cog to the bot"""
    await bot.add_cog(gdpr(bot))
