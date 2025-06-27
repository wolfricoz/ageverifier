import datetime
import logging
from abc import ABC, abstractmethod

import discord

from classes.databaseController import ConfigData, VerificationTransactions
from classes.encryption import Encryption
from classes.support.discord_tools import send_message, send_response
from views.buttons.idverifybutton import IdVerifyButton


class IdCheck(ABC) :

	@staticmethod
	@abstractmethod
	async def send_check(interaction: discord.Interaction, channel, message, age, dob, date_of_birth=None, years = None, id_check=False, verify_button=True, id_check_reason=None, server=None) :
		messages = {
			"underage" : {
				"user-message" : f"Unfortunately, you are too young to join our server. If you are 17, you may wait in the lobby until you are old enough to join.",
				"channel-message"    : f"[ID CHECK: underage] User {interaction.user.mention}\'s gave an age below 18 and was added to the ID list in {server}",
			},
			"mismatch": {
				"user-message" : f"It seems that the age you've given does not match the date of birth you've provided. Please try again. As a reminder, you must use your CURRENT age.",
				"channel-message" : f"[INFO: Age Mismatch] [Info] User {interaction.user.mention}\'s age does not match. User gave {age} (mm/dd/yyyy) but dob indicates {years}. User may retry."
			},
			"nomatch" : {
				"user-message"    : f"It seems that the age you've given does not match the date of birth you've provided. A staff member will reach out to you shortly.",
				"channel-message" : f"[ID CHECK: Age Mismatch] User {interaction.user.mention}\'s age does not match, please reach out to the user. User gave {age} (mm/dd/yyyy) but dob indicates {years} in {server}"
			},
			"dobmismatch" : {
				"user-message"    : f"It seems that the date of birth you've provided does not match a previously given date of birth. A staff member will reach out to you shortly.",
				"channel-message" : f"[ID CHECK: Age Mismatch] User {interaction.user.mention}\'s date of birth does not match. Given: {dob} (mm/dd/yyyy) Recorded: {date_of_birth} (mm/dd/yyyy) in {server}"
			},
			"idcheck":{
				"channel-message" : f"{interaction.user.mention} is on the ID list added by {server} with the reason:\n{id_check_reason}"
			}
		}
		message = messages.get(message, message)
		view = None
		if verify_button:
			view = IdVerifyButton()

		await send_message(channel,
	                   f"{f'{interaction.guild.owner.mention}' if ConfigData().get_key(interaction.guild.id, 'PINGOWNER') == 'ENABLED' else ''}{message.get('channel-message', f'No message set for {message}')}\n[Lobby Debug] Age: {age} dob {dob} userid: {interaction.user.id}", view=view)
		await send_response(interaction, message.get("user-message", "Thank you for submitting your age and date of birth, a staff member will contact you soon because of a discrepancy.")
	                    ,
	                    ephemeral=True)
		logging.info(message.get("channel-message", f"No message set for {message}"))
		if id_check and message.get("channel-message", None):
			await IdCheck.add_check(interaction, message.get("channel-message", f"No message set for {message}"))

	@staticmethod
	@abstractmethod
	async def add_check(interaction, message) :
		VerificationTransactions.set_idcheck_to_true(
			interaction.user.id,
			f"{datetime.datetime.now(datetime.timezone.utc).strftime('%m/%d/%Y')}: {message}",
			server=interaction.guild.name

		)