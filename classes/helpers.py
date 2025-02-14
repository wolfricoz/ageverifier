import logging
from datetime import datetime

import discord

from classes import databaseController
from classes.databaseController import ConfigData, UserTransactions
from classes.support.discord_tools import create_embed, send_message
from views.buttons.verifybutton import VerifyButton


async def has_onboarding(guild: discord.Guild) -> bool :
	# return 'GUILD_ONBOARDING' in guild.features
	return False


async def welcome_user(member) :
	lobby = ConfigData().get_key_int(member.guild.id, "lobby")
	channel = member.guild.get_channel(lobby)

	await add_join_roles(member)
	try :
		lobbywelcome = ConfigData().get_key(member.guild.id, "lobbywelcome")
	except databaseController.KeyNotFound :
		print(f"lobbywelcome not found for {member.guild.name}(id: {member.guild.id})")
		logging.error(f"lobbywelcome not found for {member.guild.name}(id: {member.guild.id})")
		lobbywelcome = "Lobby message not setup, please use `/config messages key:lobbywelcome action:set` to set it up. You can click the button below to verify!"
	await send_message(channel,
	                   f"Welcome {member.mention}! {lobbywelcome}"
	                   f"\n"
	                   f"-# GDPR AND INFORMATION USE DISCLOSURE: By entering your birth date (MM/DD/YYYY) and age, you consent to having this information about you stored by Age Verifier and used to verify that you are the age that you say you are, including sharing to relevant parties for age verification. This information will be stored for a maximum of 1 year if you are no longer in a server using Ageverifier.",
	                   view=VerifyButton())


async def add_join_roles(member) -> bool :
	try :
		roles = [member.guild.get_role(int(role)) for role in ConfigData().get_key_or_none(member.guild.id, "join")]
		if roles is None or len(roles) <= 0 :
			return False
		await member.add_roles(*roles)
		return True
	except discord.Forbidden :
		await send_message(member.guild.owner,
		                   f"The bot does not have permission to apply all roles to {member.mention}, please check if the bot is above the roles it is supposed to give.")
	except Exception as e :
		print(e)
		return False


def find_invite_by_code(invite_list, code) :
	"""makes an invite dictionary"""
	for inv in invite_list :
		if inv.code == code :
			return inv


async def invite_info(bot, member: discord.Member) :
	infochannel = ConfigData().get_key_or_none(member.guild.id, 'inviteinfo')
	if infochannel is None :
		logging.info(f"{member.guild.name} doesn't have invite info setup")
		return
	invites_before_join = bot.invites[member.guild.id]
	invites_after_join = await member.guild.invites()
	userdata = UserTransactions.get_user(member.id)
	for invite in invites_before_join :
		if invite.uses < find_invite_by_code(invites_after_join, invite.code).uses :
			fields = {
				"user id"            : member.id,
				"Invite Code"        : f"{invite.code}",
				"Code created by"    : f"{invite.inviter} ({invite.inviter.id})",
				"Account created at" : member.created_at.strftime("%m/%d/%Y"),
				"Member joined at"   : datetime.now().strftime("%m/%d/%Y"),
				"account flags"      : ", ".join([flag[0] for flag in member.public_flags if flag[1] is True]),
				"in database?"       : "Yes" if userdata else "No"
			}
			embed = await create_embed(
				title=f"{member.global_name} joined {member.guild.name}",
				fields=fields
			)

			try :
				embed.set_image(url=member.avatar.url)
			except :
				pass
			embed.set_footer(text=f"USERID: {member.id}")
			channel = bot.get_channel(int(infochannel))
			await send_message(channel, embed=embed)

			bot.invites[member.guild.id] = invites_after_join

			return
