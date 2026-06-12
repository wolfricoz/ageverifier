import logging
import os
from datetime import UTC, datetime, timedelta

import discord
from discord_py_utilities.messages import send_message

from classes.support.queue import Queue
from databases.transactions.ConfigData import ConfigData
from databases.transactions.ServerTransactions import ServerTransactions

DEBUG = os.getenv("DEBUG")

async def clean_lobby(bot, guild: discord.Guild, custom_days = None, clean = True, kick = True) :
	# Setup for the function; preparing the variables.
	logging.info(f"cleaning lobby for {guild.name} with variables:")
	logging.info(f" {guild.id}: clean: {clean}, kick: {kick}, custom_days: {custom_days}")
	count_messages = 0
	kicked_users = []
	lobby_channel = guild.get_channel(ConfigData().get_key_int_or_zero(guild.id, "server_join_channel"))
	mod_lobby = guild.get_channel(ConfigData().get_key_int_or_zero(guild.id, "approval_channel"))
	days = ConfigData().get_key_int_or_zero(guild.id, "clean_lobby_days")
	guild_db = ServerTransactions().get(guild.id)
	removal_message = (
		f"You have been removed from the server due to {days} days of inactivity. "
		f"If you’d like to rejoin, you’re always welcome back! Here’s a new invite link: {guild_db.invite}"
	)
	info_message = "[NOTICE] All actions are taken through the queue system, meaning you may not see immediate results. The bot may take 10m to 24 hours depending on the amount of messages.\n"
	if custom_days:
		days = custom_days

	if not lobby_channel :
		logging.warning(f"[clean-up] No lobby channel found for {guild.name}")
		return
	if days == 0 :
		logging.info(f"[clean-up] Days are set to 0, skipping {guild.name}")
		return
	removal_date = datetime.now(tz=UTC) - timedelta(days=days)

	async for message in lobby_channel.history(limit=None, before=removal_date) :
		try:
			if not message.author or not isinstance(message.author, discord.Member) :
				logging.warning(f"[clean-up] No author in {message.author}")
				count_messages += await clean_messages([message], clean)
				continue
			if not message.author.bot or message.author != bot.user or len(message.mentions) < 1 :
				continue
			if message.author != bot.user and isinstance(message.author, discord.Member) and message.author.guild_permissions.manage_messages :
				continue
			user = message.mentions[0]
			if isinstance(user, discord.Member) and user.guild_permissions.manage_messages :
				continue
			count_messages += 1
			display_name = user.global_name or user.name
			if display_name and display_name not in kicked_users:
				kicked_users.append(display_name)
			if not DEBUG :
				if kick:
					Queue().add(user.send(removal_message), 0)
					if isinstance(user, discord.Member) :
						Queue().add(user.kick(reason=f"In lobby for more than {days} days"), 0)
				count_messages += await clean_messages([message], clean)
		except Exception as e:
			logging.error(f"[clean-up] {guild.name}: {e}")
	if count_messages < 1 and len(kicked_users) < 1 :
		await send_message(mod_lobby, f"Nothing to clean up!")
		return

	if not os.path.isdir('temp') :
		os.mkdir('temp')

	if not kick and not clean:
		info_message = "[NOTICE] Ran in dry mode: No user have been kicked or messages have been removed.\n"
	await send_to_channel(mod_lobby, kicked_users, count_messages, info_message)



async def clean_messages(messages : list[discord.Message], clean):
	"""Mass delete messages without using bulk method (often because more complex logic needs to be used)"""
	if len(messages) < 1 :
		return 0
	for message in messages :
		if clean :
			Queue().add(message.delete(), 0)
	return len(messages)


async def send_to_channel(mod_lobby: discord.TextChannel, kicked_users: list, count_messages: int, info_message: str):
	with open("temp/kicked.txt", "w") as file :
		if not kicked_users:
			kicked_users = ["No users kicked"]

		str_kicked = "\n".join(str(name) if name is not None else "Unknown User" for name in kicked_users)
		file.write("=== Lobby Clean Up ===\n")
		file.write(info_message)
		file.write(f"Amount of messages to be cleaned up: {count_messages}\n")
		file.write("These users were queue'd for removal during the purge:\n")
		file.write(str_kicked)
	await mod_lobby.send(
		f"[Automatic Lobby Cleanup] cleaned up {len(kicked_users)} users and {count_messages} messages",
		file=discord.File(file.name, "autocleanup.txt")
	)
	os.remove("temp/kicked.txt")