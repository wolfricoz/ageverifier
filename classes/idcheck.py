import datetime
import logging
from abc import ABC, abstractmethod

import discord
from discord_py_utilities.messages import send_message, send_response

from classes.AgeCalculations import AgeCalculations
from databases.controllers.AgeRoleTransactions import AgeRoleTransactions
from databases.controllers.ConfigData import ConfigData
from databases.controllers.HistoryTransactions import JoinHistoryTransactions
from databases.controllers.VerificationTransactions import VerificationTransactions
from databases.current import IdVerification
from databases.enums.joinhistorystatus import JoinHistoryStatus
from resources.data.IDVerificationMessage import create_message
from views.buttons.idsubmitbutton import IdSubmitButton


class IdCheck(ABC) :

	@staticmethod
	@abstractmethod
	async def send_check(interaction: discord.Interaction, channel, message, age, dob, date_of_birth=None, years=None,
	                     id_check=False, verify_button=True, id_check_reason=None, server=None) :
		logging.debug(f"Sending ID check message for {interaction.user.id}")
		messages = {
			"underage"          : {
				"user-message"    : f"Unfortunately, you are too young to join our server. If you are 17, you may wait in the lobby until you are old enough to join.",
				"channel-message" : f"[ID CHECK: underage] User {interaction.user.mention}\'s gave an age below 18 and was added to the ID list in {server}",
			},
			"mismatch"          : {
				"user-message"    : f"It seems that the age you've given does not match the date of birth you've provided. Please try again. As a reminder, you must use your CURRENT age.",
				"channel-message" : f"[INFO: Age Mismatch] [Info] User {interaction.user.mention}\'s age does not match. User gave {age} but dob indicates {years}. User may retry."
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
				"channel-message" : f"[ID CHECK: Age Mismatch] User {interaction.user.mention}\'s age does not match, please reach out to the user. User gave {age} but dob indicates {years} in {server}"
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
			await lobbymod.send(f"Lobby Debug] Age: {age} dob {dob} userid: {interaction.user.mention}\n" + message.get('channel-message'))
			return
		if verify_button :
			from views.buttons.idverifybutton import IdVerifyButton
			view = IdVerifyButton()
		# create the embed
		embed = discord.Embed(title="ID Check Required",
		                      description=message.get('channel-message', 'No message set for this ID check.'))
		embed.add_field(name="Staff Notice",
		                value="Please contact the user to complete their ID check. They must submit a valid ID. Do not share or store the ID outside of authorized verification staff. Any abuse results in immediate blacklisting. If the issue may be a typo, you may allow a retry by removing them from the ID check list.", )
		embed.set_footer(text=f"{interaction.user.id}")

		try :
			await send_message(channel,
			                   f"{f'{interaction.guild.owner.mention}' if ConfigData().get_key(interaction.guild.id, 'PINGOWNER') == 'ENABLED' else ''} -# Lobby Debug] Age: {age} dob {dob} userid: {interaction.user.mention}",
			                   embed=embed,
			                   view=view)
			await send_response(interaction, interaction.user.mention + " " + message.get("user-message",
			                                                                              "Thank you for submitting your age and date of birth, a staff member will contact you soon because of a discrepancy.")
			                    ,
			                    ephemeral=True)
		except discord.Forbidden :
			await send_response(interaction,
			                    f"I don't have permission to send messages in {channel.mention}. Please contact a server administrator to resolve this issue.",
			                    ephemeral=True)

		if id_check and message.get("channel-message", None) :
			JoinHistoryTransactions().update(interaction.user.id, interaction.guild.id, JoinHistoryStatus.IDCHECK)
			await IdCheck.add_check(interaction.user, interaction.guild,
			                        message.get("channel-message", f"No message set for {message}"))
		await IdCheck.auto_kick(interaction.user, m_key, interaction.guild, channel)

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
		m_key = message
		message = messages.get(message, message)
		view = None

		# For the discrepancy cases that previously used send_response, DM the user and log to lobby mod channel.
		if m_key in ['mismatch', 'age_too_high', 'below_minimum_age'] :
			await send_message(user, message.get("user-message",
			                                     "There was an issue with the age and date of birth you provided. Please try again."))
			lobbymod = guild.get_channel(ConfigData().get_key_int_or_zero(guild.id, 'lobbymod'))
			if lobbymod :
				await lobbymod.send(
					f"Lobby Debug] Age: {age} dob {dob} userid: {user.mention}\n" + message.get('channel-message'))
			return

		if verify_button :
			from views.buttons.idverifybutton import IdVerifyButton
			view = IdVerifyButton()

		embed = discord.Embed(title="ID Check Required",
		                      description=message.get('channel-message', 'No message set for this ID check.'))
		embed.add_field(name="Staff Notice",
		                value="Please contact the user to complete their ID check. They must submit a valid ID. Do not share or store the ID outside of authorized verification staff. Any abuse results in immediate blacklisting. If the issue may be a typo, you may allow a retry by removing them from the ID check list.")
		embed.set_footer(text=f"{user.id}")

		try :
			await send_message(channel,
			                   f"{f'{guild.owner.mention}' if ConfigData().get_key(guild.id, 'PINGOWNER') == 'ENABLED' else ''} -# Lobby Debug] Age: {age} dob {dob} userid: {user.mention}",
			                   embed=embed,
			                   view=view)
			await send_message(user, user.mention + " " + message.get("user-message",
			                                                          "Thank you for submitting your age and date of birth, a staff member will contact you soon because of a discrepancy."))
		except discord.Forbidden :
			await send_message(user,
			                   f"I don't have permission to send messages in {channel.mention}. Please contact a server administrator to resolve this issue.")

		if id_check and message.get("channel-message", None) :
			JoinHistoryTransactions().update(user.id, guild.id, JoinHistoryStatus.IDCHECK)
			await IdCheck.add_check(user, guild, message.get("channel-message", f"No message set for {message}"))

		await IdCheck.auto_kick(user, m_key, guild, channel)

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


	@staticmethod
	@abstractmethod
	async def auto_kick(member: discord.Member, discrepancy, guild: discord.Guild, channel) :
		if discrepancy not in ['underage', 'below_minimum_age'] :
			return
		config_state = ConfigData().get_toggle(guild.id, "Autokick")
		if not config_state :
			logging.info(f'{guild.name} Autokick disabled, skipping autokick.')
			return
		logging.info('Autokick enabled')
		minimum_age = AgeRoleTransactions().get_minimum_age(guild.id)

		kick_message = (
			f"You have been removed from the server because you do not meet the minimum age requirement. You may rejoin once you meet the minimum age required of {minimum_age}."
		)
		await send_message(member, kick_message)
		await member.kick(reason=kick_message)
		await channel.send(f"[Autokick] {member.mention} doesn't meet the minimum age requirement and has been kicked.")

	@staticmethod
	@abstractmethod
	async def send_id_check(interaction: discord.Interaction, user: discord.User | discord.Member, idcheck: IdVerification):
		try:
			embed = discord.Embed(title="ID Verification", description=create_message(interaction, min_age=AgeRoleTransactions().get_minimum_age(interaction.guild.id)))
			embed.set_footer(text=f"{interaction.guild.id}")
			embed.add_field(name="ID Check", value=idcheck.reason, inline=False)

			await send_message(user, embed=embed, view=IdSubmitButton())
			await send_response(interaction, "Successfully sent ID verification request!", ephemeral=True)
		except discord.Forbidden or discord.NotFound:
			await send_response(interaction, "Could not DM user.", ephemeral=True)
		except Exception as e :
			await send_response(interaction, f"Could not DM user due to an error: {e}", ephemeral=True)