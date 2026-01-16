"""Checks the users invite info when they join and logs it"""
import logging

import discord
from discord.ext import commands
from discord_py_utilities.exceptions import NoChannelException

from classes.helpers import invite_info


class inviteInfo(commands.Cog) :
	"""
	This part of the bot works in the background to keep track of how users join your server.
	It logs which invite was used when a new member arrives.

	You can skip this topic since it's automatic and doesn't require any commands.
	"""
	def __init__(self, bot: commands.Bot) :
		self.bot = bot

	@commands.Cog.listener('on_member_join')
	async def on_member_join(self, member) :
		"""
		When a new member joins the server, this event fires to figure out which invite they used.
		It then logs this information, helping you track your server's growth and invitation sources.
		"""
		try:
			await invite_info(self.bot, member)
		except NoChannelException:
			logging.info(f'No channel found in {member.guild.name}')
			pass
	@commands.Cog.listener()
	async def on_member_remove(self, member) :
		"""
		When a member leaves or is removed, this event updates the server's internal list of active invites.
		This helps keep the invite tracking accurate.
		"""
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
