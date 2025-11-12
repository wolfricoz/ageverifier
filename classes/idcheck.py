import datetime
import logging
from abc import ABC, abstractmethod

import discord
from discord_py_utilities.messages import send_message, send_response

from databases.controllers.ConfigData import ConfigData
from databases.controllers.HistoryTransactions import JoinHistoryTransactions
from databases.controllers.VerificationTransactions import VerificationTransactions
from databases.current import IdVerification
from databases.enums.joinhistorystatus import JoinHistoryStatus


class IdCheck(ABC) :

	@staticmethod
	@abstractmethod
	async def send_check(interaction: discord.Interaction, channel, message, age, dob, date_of_birth=None, years=None,
	                     id_check=False, verify_button=True, id_check_reason=None, server=None) :
		logging.debug(f"Sending ID check message for {interaction.user.id} with date of birth: {date_of_birth}")

		messages = {
			"underage"          : {
				"user-message"    : f"Unfortunately, you are too young to join our server. If you are 17, you may wait in the lobby until you are old enough to join.",
				"channel-message" : f"[ID CHECK: underage] User {interaction.user.mention}\'s gave an age below 18 and was added to the ID list in {server}",
			},
			"mismatch"          : {
				"user-message"    : f"It seems that the age you've given does not match the date of birth you've provided. Please try again. As a reminder, you must use your CURRENT age.",
				"channel-message" : f"[INFO: Age Mismatch] [Info] User {interaction.user.mention}\'s age does not match. User gave {age} (mm/dd/yyyy) but dob indicates {years}. User may retry."
			},
			"age_too_high"      : {
				"user-message"    : (
					"The age you've entered seems unusually high. "
					"Please double-check your input and make sure you've entered your **current** age accurately."
				),
				"channel-message" : (
					f"[INFO: Age Too High] [Info] User {interaction.user.mention} entered an abnormally high age ({age}). "
					f"Date of birth indicates {years}. User may retry with correct information."
				)
			},
			"below_minimum_age" : {
				"user-message"    : (
					"You appear to be below the minimum age required to join this server. "
					"Unfortunately, you cannot proceed with verification at this time."
				),
				"channel-message" : (
					f"[INFO: Below Minimum Age] [Info] User {interaction.user.mention} appears to be below the server’s minimum age requirement. "
					f"User entered {age}, with date of birth indicating {years}. Verification process stopped."
				)
			},

			"no_match"          : {
				"user-message"    : f"It seems that the age you've given does not match the date of birth you've provided. A staff member will reach out to you shortly.",
				"channel-message" : f"[ID CHECK: Age Mismatch] User {interaction.user.mention}\'s age does not match, please reach out to the user. User gave {age} (mm/dd/yyyy) but dob indicates {years} in {server}"
			},
			"dob_mismatch"      : {
				"user-message"    : f"It seems that the date of birth you've provided does not match a previously given date of birth. A staff member will reach out to you shortly.",
				"channel-message" : f"[ID CHECK: Age Mismatch] User {interaction.user.mention}\'s date of birth does not match. Given: {dob} (mm/dd/yyyy) Recorded: {date_of_birth} (mm/dd/yyyy) in {server}"
			},
			"id_check"          : {
				"channel-message" : f"{interaction.user.mention} is on the ID list added by {server} with the reason:\n{id_check_reason}"
			}
		}
		view = None
		m_key = message
		message = messages.get(message, message)
		if m_key in ['mismatch', 'age_too_high', 'below_minimum_age'] :
			await send_response(interaction,
			                    message.get("user-message",
			                                "There was an issue with the age and date of birth you provided. Please try again."),
			                    ephemeral=True)
			lobbymod = interaction.guild.get_channel(ConfigData().get_key_int_or_zero(interaction.guild.id, 'lobbymod'))
			await lobbymod.send(message)
			return



		if verify_button :
			from views.buttons.idverifybutton import IdVerifyButton
			view = IdVerifyButton()
		try:
			await send_message(channel,
			                   f"{f'{interaction.guild.owner.mention}' if ConfigData().get_key(interaction.guild.id, 'PINGOWNER') == 'ENABLED' else ''}{message.get('channel-message', f'No message set for {message}')}\n[Lobby Debug] Age: {age} dob {dob} userid: {interaction.user.id}",
			                   view=view)
			await send_response(interaction, message.get("user-message",
			                                             "Thank you for submitting your age and date of birth, a staff member will contact you soon because of a discrepancy.")
			                    ,
			                    ephemeral=True)
		except discord.Forbidden :
			await send_response(interaction,
			                    f"I don't have permission to send messages in {channel.mention}. Please contact a server administrator to resolve this issue.",
			                    ephemeral=True)

		logging.info(message.get("channel-message", f"No message set for {message}"))
		if id_check and message.get("channel-message", None) :
			JoinHistoryTransactions().update(interaction.user.id, interaction.guild.id, JoinHistoryStatus.IDCHECK)

			await IdCheck.add_check(interaction.user, interaction.guild,
			                        message.get("channel-message", f"No message set for {message}"))

	@staticmethod
	@abstractmethod
	async def send_check_api(user, guild, channel, message, age, dob, date_of_birth=None, years=None,
	                         id_check=False, verify_button=True, id_check_reason=None, server=None) :
		messages = {
			"underage"          : {
				"user-message"    : f"Unfortunately, you are too young to join our server. If you are 17, you may wait in the lobby until you are old enough to join.",
				"channel-message" : f"[ID CHECK: underage] User {user.mention}\'s gave an age below 18 and was added to the ID list in {server}",
			},
			"mismatch"          : {
				"user-message"    : f"It seems that the age you've given does not match the date of birth you've provided. Please try again. As a reminder, you must use your CURRENT age.",
				"channel-message" : f"[INFO: Age Mismatch] [Info] User {user.mention}\'s age does not match. User gave {age} (mm/dd/yyyy) but dob indicates {years}. User may retry."
			},
			"age_too_high"      : {
				"user-message"    : (
					"The age you've entered seems unusually high. "
					"Please double-check your input and make sure you've entered your **current** age accurately."
				),
				"channel-message" : (
					f"[INFO: Age Too High] [Info] User {user.mention} entered an abnormally high age ({age}). "
					f"Date of birth indicates {years}. User may retry with correct information."
				)
			},
			"below_minimum_age" : {
				"user-message"    : (
					"You appear to be below the minimum age required to join this server. "
					"Unfortunately, you cannot proceed with verification at this time."
				),
				"channel-message" : (
					f"[INFO: Below Minimum Age] [Info] User {user.mention} appears to be below the server’s minimum age requirement. "
					f"User entered {age}, with date of birth indicating {years}. Verification process stopped."
				)
			},

			"no_match"          : {
				"user-message"    : f"It seems that the age you've given does not match the date of birth you've provided. A staff member will reach out to you shortly.",
				"channel-message" : f"[ID CHECK: Age Mismatch] User {user.mention}\'s age does not match, please reach out to the user. User gave {age} (mm/dd/yyyy) but dob indicates {years} in {server}"
			},
			"dob_mismatch"      : {
				"user-message"    : f"It seems that the date of birth you've provided does not match a previously given date of birth. A staff member will reach out to you shortly.",
				"channel-message" : f"[ID CHECK: Age Mismatch] User {user.mention}\'s date of birth does not match. Given: {dob} (mm/dd/yyyy) Recorded: {date_of_birth} (mm/dd/yyyy) in {server}"
			},
			"id_check"          : {
				"channel-message" : f"{user.mention} is on the ID list added by {server} with the reason:\n{id_check_reason}"
			}
		}
		message = messages.get(message, message)
		view = None
		if verify_button :
			from views.buttons.idverifybutton import IdVerifyButton
			view = IdVerifyButton()

		await send_message(channel,
		                   f"{f'{guild.owner.mention}' if ConfigData().get_key(guild.id, 'PINGOWNER') == 'ENABLED' else ''}{message.get('channel-message', f'No message set for {message}')}\n[Lobby Debug] Age: {age} dob {dob} userid: {user.id}",
		                   view=view)
		logging.info(message.get("channel-message", f"No message set for {message}"))
		if id_check and message.get("channel-message", None) :
			JoinHistoryTransactions().update(user.id, guild.id, JoinHistoryStatus.IDCHECK)

			await IdCheck.add_check(user, guild, message.get("channel-message", f"No message set for {message}"))

	@staticmethod
	@abstractmethod
	async def add_check(user, guild, message) :
		VerificationTransactions().set_idcheck_to_true(
			user.id,
			f"{datetime.datetime.now(datetime.timezone.utc).strftime('%m/%d/%Y')}: {message}",
			server=guild.name

		)


	@staticmethod
	@abstractmethod
	async def remove_idmessage(user: discord.User | discord.Member, idcheck: IdVerification) :
		try :
			dm_channel = user.dm_channel or await user.create_dm()
			message_to_delete = await dm_channel.fetch_message(idcheck.idmessage)
			await message_to_delete.delete()
			VerificationTransactions().remove_idmessage(user.id)
		except Exception :
			pass

