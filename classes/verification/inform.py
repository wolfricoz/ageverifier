import logging

import discord
from discord_py_utilities.messages import send_message

from classes.support.queue import Queue
from databases.transactions.ConfigData import ConfigData


async def notify_agecheck(bot, current_guild, member, embed):
	embed.add_field(name="Server", value=current_guild.name, inline=False)
	embed.add_field(name="No Buttons", value="To prevent spamming the user with ID requests, this notice has no buttons.", inline=False)

	await inform_servers(bot, current_guild, member, f"[Verify Fail: Cross-server] User was flagged for an ID check in another server.", embed)


async def notify_verified(bot, current_guild: discord. Guild, member:discord.Member):
	await inform_servers(bot, current_guild, member, f"[ID verify: Cross-server]{member.name} has been ID verified in {current_guild.name}!", )



async def inform_servers(bot, current_guild: discord.Guild,  member: discord.Member, msg: str = " ", embed: discord.Embed = None):
	"""
	This function informs servers, this can be used in multiple ways.
	:param bot:
	:param current_guild:
	:param member:
	:param msg:
	:param embed:
	"""
	for guild in bot.guilds :
		if not member in guild.members :
			continue
		if guild == current_guild :
			# Prevent double notifications
			continue
		try:
			verify_fail_channel = ConfigData().get_channel(guild, "verification_failure_log")
			Queue().add(send_message(verify_fail_channel, msg, embed=embed))

		except Exception as e:
			logging.warning(f"Failed to inform {guild.name} about verification failure from another server.")



