"""Checks the users invite info when they join and logs it"""
from datetime import datetime

import discord
from discord.ext import commands

from classes.databaseController import ConfigData
from classes.helpers import has_onboarding, invite_info


class inviteInfo(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener('on_member_join')
    async def on_member_join(self, member):
        """reads invite dictionary, and outputs user info"""
        if await has_onboarding(member.guild):
            return
        await invite_info(self.bot, member)



    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """removes member's invites"""
        try:
            self.bot.invites[member.guild.id] = await member.guild.invites()
        except discord.NotFound:
            pass


async def setup(bot):
    """Adds cog to the bot"""
    await bot.add_cog(inviteInfo(bot))
