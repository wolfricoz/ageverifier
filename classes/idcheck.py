import datetime
import logging
from abc import ABC, abstractmethod

from classes.databaseController import VerificationTransactions
from classes.support.discord_tools import send_message, send_response


class IdCheck(ABC) :

	@staticmethod
	@abstractmethod
	async def send_check(interaction, channel, message, age, dob, years = None, id_check=False) :
		messages = {
			"underage" : {
				"user-message"    : f"[ID CHECK: underage] User {interaction.user.mention}\'s gave an age below 18 and was added to the ID list.",
				"channel-message" : f"Unfortunately you are too young for our server. If you are 17 you may wait in the lobby."
			},
			"mismatch": {
				"user-message" : f"It seems your age does not match the date of birth you provided. Please try again. Please use your CURRENT age.",
				"channel-message" : f"[INFO: Age Mismatch] [Info] User {interaction.user.mention}\'s age does not match. User gave {age} but dob indicates {years}. User may retry."
			},
			"nomatch" : {
				"user-message"    : f"It seems your age does not match the date of birth you provided. A staff member will reach out to you.",
				"channel-message" : f"[INFO: Age Mismatch] [Info] User {interaction.user.mention}\'s age does not match, please reach out to the user. User gave {age} but dob indicates {years}"
			},


		}
		message = messages.get(message, message)
		await send_message(channel,
	                   f"{message.get("channel-message", f"No message set for {message}")}\n[Lobby Debug] Age: {age} dob {dob} userid: {interaction.user.id}")
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
			f"{datetime.datetime.now(datetime.timezone.utc).strftime('%m/%d/%Y')}: {message}")