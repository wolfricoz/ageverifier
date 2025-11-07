"""Checks the users invite info when they join and logs it"""
import logging

import discord
from discord.ext import commands
from discord_py_utilities.exceptions import NoChannelException

from classes.helpers import invite_info


class inviteInfo(commands.Cog) :
	def __init__(self, bot: commands.Bot) :
		self.bot = bot

	@commands.Cog.listener('on_member_join')
	async def on_member_join(self, member) :
		"""reads invite dictionary, and outputs user info"""
		try:
			await invite_info(self.bot, member)
		except NoChannelException:
			logging.info(f'No channel found in {member.guild.name}')
			pass
	@commands.Cog.listener()
	async def on_member_remove(self, member) :
		"""removes member's invites"""
		try :
			self.bot.invites[member.guild.id] = await member.guild.invites()
		except discord.Forbidden:
			logging.info(f'No access to fetch invites in {member.guild.name}')
			pass
		except discord.NotFound:
			pass


async def setup(bot) :
	"""Adds cog to the bot"""
	await bot.add_cog(inviteInfo(bot))
