import logging
import os
from datetime import UTC, datetime, timedelta

import discord

from classes.support.queue import Queue
from databases.transactions.ConfigData import ConfigData
from databases.transactions.ServerTransactions import ServerTransactions

DEBUG = os.getenv("DEBUG")

async def clean_lobby(bot, guild: discord.Guild, custom_days = None) :
	# Setup for the function; preparing the variables.
	logging.info(f"cleaning lobby for {guild.name}")
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
			logging.info(f"Message: {message.content}")
			if not message.author or not isinstance(message.author, discord.Member) :
				logging.warning(f"[clean-up] No author in {message.author}")
				Queue().add(message.delete())
				continue
			if not message.author.bot or message.author != bot.user or len(message.mentions) < 1 :
				continue
			if message.author != bot.user and isinstance(message.author, discord.Member) and message.author.guild_permissions.manage_messages :
				continue
			user = message.mentions[0]
			if isinstance(user, discord.Member) and user.guild_permissions.manage_messages :
				continue
			count_messages += 1
			if user.global_name not in kicked_users :
				kicked_users.append(user.global_name)
			if not DEBUG :
				Queue().add(user.send(removal_message), 0)
				if isinstance(user, discord.Member) :
					Queue().add(user.kick(reason=f"In lobby for more than {days} days"), 0)
				Queue().add(message.delete(), 0)
		except Exception as e:
			logging.error(f"[clean-up] {guild.name}: {e}")
	if count_messages < 1 and len(kicked_users) < 1 :
		return

	if not os.path.isdir('temp') :
		os.mkdir('temp')

	with open("temp/kicked.txt", "w") as file :
		if not kicked_users:
			kicked_users = ["No users kicked"]

		str_kicked = "\n".join(kicked_users)
		file.write("These users were queue'd for removal during the purge:\n")
		file.write(str_kicked)
	await mod_lobby.send(
		f"[Automatic Lobby Cleanup] cleaned up {len(kicked_users)} users and {count_messages} messages",
		file=discord.File(file.name, "autocleanup.txt")
	)
	os.remove("temp/kicked.txt")
