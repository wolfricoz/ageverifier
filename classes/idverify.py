import logging
import os

import discord
from classes.retired.discord_tools import send_message, send_response

from classes.AgeCalculations import AgeCalculations
from classes.lobbyprocess import LobbyProcess
from classes.support.queue import Queue
from classes.verification.inform import notify_verified
from databases.transactions.ConfigData import ConfigData
from databases.transactions.VerificationTransactions import VerificationTransactions


async def verify(user: discord.Member, interaction: discord.Interaction, dob: str, process=True, reverify=False) -> None :
	if await check_staff_status(interaction, user):
		return await send_response(interaction,
		                    f"[CANNOT_VERIFY_STAFF] You cannot verify staff members using this command, if they wish to be verified they can open a ticket on the support guild. Attempting to circumvent this guideline will result in permanent blacklisting of all users involved.", )

	if not interaction.user.guild_permissions.administrator:
		return False
	VerificationTransactions().idverify_update(user.id, dob, interaction.guild.name, server=interaction.guild.name)
	age = AgeCalculations.dob_to_age(dob)
	dev_log = interaction.client.get_channel(int(os.getenv("DEV")))
	if dev_log is None:
		dev_log = await interaction.client.fetch_channel(int(os.getenv("DEV", 1022319186950758472)))
	id_message = f"**USER ID VERIFICATION**\n**ID VERIFIED BY:** {interaction.user}\n"
	await notify_verified(interaction.client, interaction.guild, user)

	await LobbyProcess.log(user, interaction.guild, age, dob, interaction.user, True, id_verify=id_message, reverify=reverify)
	await interaction.channel.send(
		f"{user.mention} has been ID verified with `{dob}` by {interaction.user.mention}")
	if not process :
		return None
	if interaction.guild is None:
		return None

	await LobbyProcess.approve_user(interaction.guild, user, dob, age, interaction.user.name, idverify=True, reverify=reverify)
	if not dev_log:
		return None
	await send_message(dev_log, f"{user.global_name} ({user.id}) has been ID verified by {interaction.user} in {interaction.guild.name}!")
	return None


async def check_staff_status(interaction: discord.Interaction, member: discord.Member)->bool:
	if member.guild_permissions.manage_guild or member.guild_permissions.manage_permissions or member.guild_permissions.manage_messages or member.guild_permissions.manage_roles or member.guild_permissions.kick_members or member.guild_permissions.ban_members or member.guild_permissions.administrator :
		return True
	if interaction.guild.owner_id == member.id :
		return True
	return False



async def check_servers(interaction: discord.Interaction, member: discord.Member)->bool:
	# Future: [QUALITY] Iterating every guild the bot is in for one member is O(guilds); this scales poorly as the bot grows.
	# Potential fix: Use join history to find guilds user joined.
	for guild in interaction.client.guilds :
		try:
			channel = await ConfigData().get_channel(guild, "verification_failure_log")
			if member in guild.members :
				Queue().add(send_message(channel, f"{member.global_name} ({member.id}) has been ID verified by {interaction.user} in {interaction.guild.name}!"))
		except Exception as e:
			logging.warning(f"Failed to inform server {e}")