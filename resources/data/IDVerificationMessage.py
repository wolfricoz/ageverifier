from datetime import datetime

import discord


def create_message(interaction: discord.Interaction, min_age, user_init=False) :
	# Header
	message = "## Age Verification\n"
	message += "Hi, to verify your age we'd like to request you to ID.\n\n"

	# Logic: user_init means they clicked it. Else means there was a discrepancy.
	if user_init :
		message += (
			"**Why do I have to ID?**\n"
			"You are seeing this because you requested to verify your identity using ID. "
			"Please follow the prompts below to complete the secure verification system and unlock the rest of the server.\n"
		)
	else :
		message += (
			"**Why do I have to ID?**\n"
			f"There has been a discrepancy with your date of birth and/or age which we feel requires additional verification, "
			f"this is to verify that you are above the age minimum age of the server ({min_age}).\n"
		)

	# Note/Decline Section
	message += (
		"\nIf you feel uncomfortable you may press the decline button to do so; "
		"however we reserve the right to decline you access to our server.\n\n"
	)

	# Instructions Section
	message += (
		"### Instructions\n"
		f"* **Black out everything except your date of birth**\n"
		f"* Include a note with `{interaction.guild.name.split(' ')[0]}{datetime.now().strftime('%Y')}` and your username written on it.\n"
		f"* **__After verification please remove your ID.__**\n"
		f"* After staff verifies your date of birth, the bot will remove all traces of your ID from its system.\n\n"
		"**__We may retain your blacked out ID for a maximum of 7 days for the server to complete this verification. "
		"Your ID is strictly used for verification purposes only__**\n\n"
		"If you verify successfully, you will be granted access to the server and you will not need to ID again "
		"for any servers using AgeVerifier."
	)

	return message