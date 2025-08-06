"""this module handles the lobby."""

import discord
from discord.ext import commands

from classes.helpers import has_onboarding, welcome_user
from databases.controllers.UserTransactions import UserTransactions
from views.buttons.approvalbuttons import ApprovalButtons
from views.buttons.dobentrybutton import dobentry
from views.buttons.verifybutton import VerifyButton


class LobbyEvents(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.index = 0
        self.bot.add_view(VerifyButton())
        self.bot.add_view(ApprovalButtons())
        self.bot.add_view(dobentry())



    @commands.Cog.listener('on_member_join')
    async def add_to_db(self, member):
        UserTransactions().add_user_empty(member.id)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """posts the button for the user to verify with."""
        if await has_onboarding(member.guild):
            return
        await welcome_user(member)

    # @commands.Cog.listener()
    # async def on_member_update(self, before: discord.Member, after: discord.Member):
    #     if before.flags != after.flags:
    #         # Perform the desired action when the member's flags change
    #         if before.flags.completed_onboarding is False and after.flags.completed_onboarding is True:
    #             await welcome_user(after)
    #             await invite_info(self.bot, after)


async def setup(bot):
    """Adds the cog to the bot."""
    await bot.add_cog(LobbyEvents(bot))
