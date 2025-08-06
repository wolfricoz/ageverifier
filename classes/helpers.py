import logging
from datetime import datetime

import discord
from discord_py_utilities.permissions import find_first_accessible_text_channel

import databases.exceptions.KeyNotFound
from classes.retired.discord_tools import create_embed
from databases.controllers.ConfigData import ConfigData
from databases.controllers.UserTransactions import UserTransactions
from discord_py_utilities.messages import send_message
from views.buttons.verifybutton import VerifyButton


async def has_onboarding(guild: discord.Guild) -> bool :
	# return 'GUILD_ONBOARDING' in guild.features
	return False


async def welcome_user(member) :
	warning = ""
	lobby = ConfigData().get_key_int_or_zero(member.guild.id, "lobby")
	channel = member.guild.get_channel(lobby)
	if channel is None:
		warning = "WARNING: Lobby channel not set, please configure your lobby with `/config channels`"
		channel = find_first_accessible_text_channel(member.guild)
	await add_join_roles(member)
	welcome_enabled = ConfigData().get_key(member.guild.id, "lobbywelcome", "enabled")
	if welcome_enabled.lower() == "disabled" :
		return
	try :
		lobby_welcome = ConfigData().get_key(member.guild.id, "lobbywelcome")
	except databases.exceptions.KeyNotFound.KeyNotFound :
		print(f"lobbywelcome not found for {member.guild.name}(id: {member.guild.id})")
		logging.error(f"lobbywelcome not found for {member.guild.name}(id: {member.guild.id})")
		lobby_welcome = "Lobby message not setup, please use `/config messages key:lobbywelcome action:set` to set it up. You can click the button below to verify!"
	await send_message(channel,
	                   f"Welcome {member.mention}! {lobby_welcome}\n{warning}"
	                   f"\n"
	                   f"-# GDPR AND INFORMATION USE DISCLOSURE: By entering your birth date (MM/DD/YYYY) and age, you consent to having this information about you stored by Age Verifier and used to verify that you are the age that you say you are, including sharing to relevant parties for age verification. This information will be stored for a maximum of 1 year if you are no longer in a server using Ageverifier.",
	                   view=VerifyButton(), error_mode="ignore")


async def add_join_roles(member) -> bool:
	try :
		roles = [member.guild.get_role(int(role)) for role in ConfigData().get_key_or_none(member.guild.id, "join")]
		if roles is None or len(roles) <= 0 :
			return False
		await member.add_roles(*roles)
		return True
	except discord.Forbidden :
		await send_message(member.guild.owner,
		                   f"The bot does not have permission to apply all roles to {member.mention}, please check if the bot is above the roles it is supposed to give.")
		return False
	except Exception as e :
		print(e)
		return False


def find_invite_by_code(invite_list, code) :
	"""makes an invite dictionary"""
	for inv in invite_list :
		if inv.code == code :
			return inv
	return None

async def invite_info(bot, member: discord.Member) :
	infochannel = ConfigData().get_key_or_none(member.guild.id, 'inviteinfo')
	if infochannel is None :
		logging.info(f"{member.guild.name} doesn't have invite info setup")
		return
	invites_before_join = bot.invites[member.guild.id]
	invites_after_join = await member.guild.invites()
	userdata = UserTransactions().get_user(member.id)
	fields = {
		"user id"            : member.id,
		"Invite Code"        : "No invite found",
		"Code created by"    : "No invite found",
		"Account created at" : member.created_at.strftime("%m/%d/%Y"),
		"Member joined at"   : datetime.now().strftime("%m/%d/%Y"),
		"account flags"      : ", ".join([flag[0] for flag in member.public_flags if flag[1] is True]),
		"in database?"       : "Yes" if userdata else "No"
	}
	try:
		for invite in invites_before_join :
			if invite is None:
				continue
			if invite.uses < find_invite_by_code(invites_after_join, invite.code).uses :
				fields["Invite Code"] = invite.code
				fields["Code created by"] = invite.inviter.name
				bot.invites[member.guild.id] = invites_after_join
	except Exception as e :
		logging.error(e, exc_info=True)
	embed = await create_embed(
		title=f"{member.name} joined {member.guild.name}",
		fields=fields
	)
	try :
		embed.set_image(url=member.avatar.url)
	except :
		pass
	channel = bot.get_channel(int(infochannel))
	await send_message(channel, embed=embed)
