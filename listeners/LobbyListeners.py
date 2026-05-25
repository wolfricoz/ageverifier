import logging

from discord import Member
from discord.ext.commands import Bot, Cog, GroupCog
from discord_py_utilities.messages import send_message

from classes.lobby.JoinRequirements import JoinRequirements
from databases.transactions.ConfigData import ConfigData


class LobbyListeners(GroupCog) :

	def __init__(self, bot: Bot) :
		self.bot = bot

	@Cog.listener("on_member_join")
	async def requirements_check(self, member: Member) -> None:
		"""Checks if the user has the minimum requirements to join the server, to improve user quality."""
		logging.info("LobbyListeners: Checking on join")
		checker = JoinRequirements(self.bot, member)
		await checker.evaluate()


	@Cog.listener("on_member_remove")
	async def on_member_remove(self, member: Member) -> None :
		"""Handles the user leaving the server."""
		enabled = ConfigData().get_toggle(member.guild.id, "SEND_LEAVE_MESSAGE")
		if not enabled :
			return
		leave_message = ConfigData().get_key(member.guild.id, "server_leave_message", f"...")
		channel = await ConfigData().get_channel(member.guild, "leave_log")
		if not channel:
			return
		await send_message(channel, f"{member.mention} has left" + leave_message)





async def setup(bot: Bot) :
	await bot.add_cog(
		LobbyListeners(bot),
	)
