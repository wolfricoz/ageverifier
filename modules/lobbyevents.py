"""this module handles the lobby."""

import discord
from discord.ext import commands

from classes.helpers import has_onboarding, welcome_user
from databases.enums.joinhistorystatus import JoinHistoryStatus
from databases.transactions.HistoryTransactions import JoinHistoryTransactions
from databases.transactions.UserTransactions import UserTransactions


class LobbyEvents(commands.Cog) :
	"""
	This module handles automated events related to members joining and leaving the server.
	It works in the background to manage the initial state of new members and log their activity.
	"""
	def __init__(self, bot: commands.Bot) :
		self.bot = bot
		self.index = 0


	@commands.Cog.listener('on_member_join')
	async def add_to_db(self, member) :
		"""
		When a new member joins, this event automatically creates a basic entry for them in the user database.
		This ensures they are ready for the verification process.
		"""
		UserTransactions().add_user_empty(member.id)

	@commands.Cog.listener()
	async def on_member_join(self, member: discord.Member) :
		"""
		This event welcomes a new member to the server by sending the verification message in the lobby.
		This doesn't run if the server is using Discord's built-in Onboarding feature.
		"""
		if await has_onboarding(member.guild) :
			return
		await welcome_user(member)

	@commands.Cog.listener()
	async def on_member_remove(self, member: discord.Member) :
		"""
		When a member leaves, this event updates their join history.
		If they left before completing verification, their status is marked as 'FAILED'. This helps with server analytics and moderation.
		"""
		joinhistory = JoinHistoryTransactions().get(member.id, member.guild.id)
		if joinhistory is None:
			return
		if joinhistory.status != JoinHistoryStatus.NEW:
			return
		JoinHistoryTransactions().update(member.id, member.guild.id, status=JoinHistoryStatus.FAILED)





	# @commands.Cog.listener()
	# async def on_member_update(self, before: discord.Member, after: discord.Member):
	#     if before.flags != after.flags:
	#         # Perform the desired action when the member's flags change
	#         if before.flags.completed_onboarding is False and after.flags.completed_onboarding is True:
	#             await welcome_user(after)
	#             await invite_info(self.bot, after)


async def setup(bot) :
	"""Adds the cog to the bot."""
	await bot.add_cog(LobbyEvents(bot))
