import datetime
import os
import re
from abc import ABC, abstractmethod

import discord
from discord.utils import get
from discord_py_utilities.permissions import find_first_accessible_text_channel
from pytz.reference import first_sunday_on_or_after

from classes.AgeCalculations import AgeCalculations
from classes.ageroles import change_age_roles
from databases.transactions.ConfigData import ConfigData
from databases.transactions.ConfigTransactions import ConfigTransactions
from databases.transactions.HistoryTransactions import JoinHistoryTransactions
from databases.transactions.UserTransactions import UserTransactions
from discord_py_utilities.messages import send_message
from classes.support.queue import Queue
from classes.whitelist import check_whitelist
from databases.enums.joinhistorystatus import JoinHistoryStatus
from databases.exceptions.KeyNotFound import KeyNotFound


class LobbyProcess(ABC) :

	@staticmethod
	@abstractmethod
	async def approve_user(guild, user, dob, age, staff, idverify = False, reverify=False) :
		# checks if user is on the id list
		id_msg = ""
		if await AgeCalculations.id_check(guild, user) :
			return
		# updates user's age if it exists, otherwise makes a new entry
		exists = UserTransactions().update_user_dob(user.id, dob, guild.name, override=True)

		# changes user's roles; adds


		Queue().add(change_age_roles(guild, user, age, remove=reverify, reverify=reverify), priority=2)

		# Log age and dob to lobbylog
		if idverify:
			id_msg = "**ID VERIFIED**\n"
		Queue().add(LobbyProcess.log(user, guild, age, dob, staff, exists, id_verify=id_msg , reverify=reverify), priority=2)
		if not reverify :
		# fetches welcoming message and welcomes them in general channel

			Queue().add(LobbyProcess.welcome(user, guild), priority=2)

		# changes user's roles; removes - Moved here to give some time between adding and removing roles (potential fixing a discord syncing bug)

			Queue().add(LobbyProcess.remove_user_roles(user, guild), priority=2)

		# Cleans up the messages in the lobby and where the command was executed
		Queue().add(LobbyProcess.clean_up(guild, user), priority=0)

	@staticmethod
	@abstractmethod
	async def remove_user_roles(user, guild: discord.Guild) :
		if isinstance(user, discord.User) :
			user = guild.get_member(user.id)
		config_rem_roles = ConfigData().get_key(guild.id, "REM")
		rem_roles = await LobbyProcess.get_roles(guild, config_rem_roles, "REM")
		Queue().add(user.remove_roles(*rem_roles), priority=2)




	@staticmethod
	@abstractmethod
	async def get_roles(guild, roles, key: str) :
		results = []
		for role in roles :
			verrole = get(guild.roles, id=int(role))
			if verrole is None :
				ConfigTransactions().config_key_remove(guildid=guild.id, key=key.upper(), value=role)
				await guild.owner.send(f"Role {role} couldn't be found and has been removed from the config in {guild.name}")
				continue
			results.append(verrole)
		return results


	@staticmethod
	@abstractmethod
	async def log(user, guild, age, dob, staff, exists, id_verify = "", reverify=False) :
		# Empty variables, these may be filled based on the type of verification
		dob_field = ""
		reverify_field = ""

		lobbylog = ConfigData().get_key(guild.id, "lobbylog")
		if reverify:
			revlog = ConfigData().get_key(guild.id, "reverifylog")
			if revlog is not None:
				lobbylog = revlog

		channel = guild.get_channel(int(lobbylog))
		if check_whitelist(guild.id) :
			dob_field = f"DOB: {dob} \n"
		if reverify:
			reverify_field = "[REVERIFICATION]\n"
		if isinstance(user, discord.User) :
			user = guild.get_member(user.id)


		message = await send_message(channel, f"{id_verify}"
		                            f"{reverify_field}"
		                            f"user: {user.mention}\n"
		                            f"Age: {age} \n"
		                            f"{dob_field}"
		                            f"User info: \n"
		                            f"UID: {user.id} \n"
		                            f"Joined at: {user.joined_at.strftime('%m/%d/%Y %I:%M:%S %p') if user.joined_at else 'None'} \n"
		                            f"Account created at: {user.created_at.strftime('%m/%d/%Y %I:%M:%S %p')} \n"
		                            f"Executed at: {datetime.datetime.now().strftime('%m/%d/%Y %I:%M:%S %p')} \n"
		                            f"first time: {f'yes' if not exists else 'no'}\n"
		                            f"Staff: {staff}")
		if id_verify :
			JoinHistoryTransactions().update(user.id, guild.id, JoinHistoryStatus.VERIFIED,
			                                 verification_date=datetime.datetime.now(), message_id=message.id)
			return
		JoinHistoryTransactions().update(user.id, guild.id, JoinHistoryStatus.SUCCESS, verification_date=datetime.datetime.now(), message_id=message.id)


	@staticmethod
	@abstractmethod
	async def clean_up(guild, user) :
		lobby = ConfigData().get_key(guild.id, "lobby")
		lobbymod = ConfigData().get_key(guild.id, "lobbymod")
		channel = guild.get_channel(int(lobby))
		messages = channel.history(limit=100)
		notify = re.compile(r"Info", flags=re.IGNORECASE)
		count = 0
		async for message in messages :
			if message.author == user or user in message.mentions and count < 10 :
				count += 1
				Queue().add(message.delete(), priority=0)
		channel = guild.get_channel(int(lobbymod))
		messages = channel.history(limit=100)
		count = 0
		async for message in messages :
			if user in message.mentions and count < 5 :
				if message.author.bot :
					notify_match = notify.search(message.content)
					if notify_match is not None :
						pass
					else :
						count += 1
						Queue().add(message.delete(), priority=0)

	@staticmethod
	@abstractmethod
	async def welcome(user: discord.Member, guild: discord.Guild) :
		if ConfigData().get_key(guild.id, "welcome") == "DISABLED" :
			return
		general = ConfigData().get_key(guild.id, "general")
		message = ConfigData().get_key(guild.id, "welcomemessage")
		channel = guild.get_channel(int(general))
		if channel is None:
			channel = await guild.fetch_channel(int(general))

		async for cmessage in channel.history(limit=20) :
			if cmessage.author.bot and user in cmessage.mentions :
				return
		await send_message(channel, f"Welcome to {guild.name} {user.mention}! {message}")

	@staticmethod
	@abstractmethod
	async def age_log(userid, dob, interaction, operation="added", log=True, reason="") :
		try:
			age_log = interaction.guild.get_channel(ConfigData().get_key_int(interaction.guild.id, "lobbylog"))
		except KeyNotFound:
			age_log = find_first_accessible_text_channel(interaction.guild)
			await send_message(age_log, f"Could not find age log channel, using {age_log.mention} instead. Please set one up with `/config channels`")
			return
		dev_channel = interaction.client.get_channel(int(os.getenv('DEV')))
		dob_field = ""
		if check_whitelist(interaction.guild.id) :
			dob_field = f"DOB: {dob}\n"
		Queue().add(send_message(dev_channel,
		                   f"{userid}'s dob {operation} in {interaction.guild.name} by {interaction.user.name}. {f'Reason: {reason}' if reason else ''}"), 0)
		await send_message(age_log, f"USER {operation.upper()}\n"
		                                    f"{dob_field}"
		                                    f"UID: {userid}\n"
		                                    f"Entry updated by: {interaction.user.name}")
		Queue().add(send_message(interaction.channel, f"{operation} <@{userid}>({userid}) date of birth with dob: {dob}"))



