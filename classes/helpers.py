import logging
from datetime import datetime

import discord
from discord_py_utilities.messages import send_message
from discord_py_utilities.permissions import check_missing_channel_permissions, find_first_accessible_text_channel

import databases.exceptions.KeyNotFound
from classes.permissions_notice import PermissionNotice
from databases.enums.joinhistorystatus import JoinHistoryStatus
from databases.transactions.ConfigData import ConfigData
from databases.transactions.HistoryTransactions import JoinHistoryTransactions
from databases.transactions.UserTransactions import UserTransactions
from views.buttons.verifybutton import GDPR_DISCLOSURE, VerifyButton


async def has_onboarding(guild: discord.Guild) -> bool :
	# return 'GUILD_ONBOARDING' in guild.features
	return False


async def welcome_user(member) :
	logging.info("Welcoming user " + str(member.id) + " to " + str(member.guild.id))
	JoinHistoryTransactions().add(member.id, member.guild.id, JoinHistoryStatus.NEW)
	warning = ""
	lobby = ConfigData().get_key_int_or_zero(member.guild.id, "server_join_channel")
	channel = member.guild.get_channel_or_thread(lobby)
	if channel is None:
		warning = "WARNING: Lobby channel not set, please configure your lobby with `/config channels`"
		channel = find_first_accessible_text_channel(member.guild)
	await add_join_roles(member)
	welcome_enabled = ConfigData().get_key(member.guild.id, "send_join_message", "enabled")
	if welcome_enabled.lower() == "disabled" :
		return
	try :
		lobby_welcome = ConfigData().get_key(member.guild.id, "server_join_message",
		                                     "Lobby message not setup, please use `/config messages key:server_join_message action:set` to set it up. You can click the button below to verify!")
	except databases.exceptions.KeyNotFound.KeyNotFound :
		print(f"lobbywelcome not found for {member.guild.name}(id: {member.guild.id})")
		logging.error(f"lobbywelcome not found for {member.guild.name}(id: {member.guild.id})")
		lobby_welcome = "Lobby message not setup, please use `/config messages key:server_join_message action:set` to set it up. You can click the button below to verify!"
	if channel is None :
		channel = find_first_accessible_text_channel(member.guild)
		if channel is None :
			logging.info("Lobby channel not found, and no accessible text channel found to send welcome message.")
			return
		warning = f"Lobby channel not found, sending to {channel.mention} instead."

	missing = check_missing_channel_permissions(channel, ["view_channel", "send_messages", "embed_links"])
	if missing :
		# Without these the lobby has no verify button, so nobody can start verification.
		await PermissionNotice.notify(member.guild, channel=channel, missing=missing,
		                              purpose="post the welcome message and verify button in the lobby")
		return
	await send_message(channel,
	                   f"Welcome {member.mention}! {lobby_welcome}\n{warning}"
	                   f"\n{GDPR_DISCLOSURE}",
	                   view=VerifyButton(member.guild.id), error_mode="ignore")


async def add_join_roles(member) -> bool:
	try :
		roles = [member.guild.get_role(int(role)) for role in
		         ConfigData().get_key_or_none(member.guild.id, "server_join_role")]
		if roles is None or len(roles) <= 0 :
			return False
		await member.add_roles(*roles)
		return True
	except discord.Forbidden :
		# Manage Roles is off, or a join role sits above Ageverifier's; the notice's hierarchy step covers the second.
		await PermissionNotice.notify(member.guild, missing=["manage_roles"],
		                              purpose="give new members the roles set as server_join_role")
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


async def create_embed(title, fields) :
	embed = discord.Embed(title=title)
	for key, value in fields.items() :
		embed.add_field(name=key, value=value, inline=False)
	return embed


async def invite_info(bot, member: discord.Member) :
	infochannel = ConfigData().get_channel_id(member.guild.id, 'invite_log')
	if infochannel is None :
		logging.info(f"{member.guild.name} doesn't have invite info setup")
		return
	if member.guild.id not in bot.invites:
		bot.invites[member.guild.id] = {}
	invites_before_join = bot.invites[member.guild.id]
	try :
		invites_after_join = await member.guild.invites()
	except discord.Forbidden :
		await PermissionNotice.notify(member.guild, missing=["manage_guild"],
		                              purpose="read invite data for invite logging")
		return
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
		logging.warning(e)
	embed = await create_embed(
		title=f"{member.name} joined {member.guild.name}",
		fields=fields
	)
	try :
		embed.set_image(url=member.avatar.url)
	except :
		pass
	channel = bot.get_channel(infochannel)
	if channel is None :
		logging.info(f"{member.guild.name}'s invite_log channel {infochannel} no longer exists")
		return
	await send_message(channel, embed=embed, error_mode="ignore")


async def fetch_member(guild: discord.Guild, user_id:int) -> discord.Member | None:
	member = guild.get_member(user_id)
	if member is None :
		try :
			member = await guild.fetch_member(user_id)
		except Exception as e :
			logging.error(e, exc_info=True)
			return None
	return member