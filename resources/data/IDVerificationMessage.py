from datetime import datetime

import discord


def create_message(interaction: discord.Interaction, min_age) :
	return (
f"""Hi, to verify your age we'd like to request you to ID.

**Why do I have to ID?**
There has been a discrepancy with your date of birth and/or age which we feel requires additional verification, this is to verify that you are above the age minimum age of the server ({min_age}).

If you feel uncomfortable you may press the decline button to do so; however we reserve the right to decline you access to our server.

**Instructions**
- **Black out everything except your date of birth**
- Include a note with `{interaction.guild.name.split(" ")[0]}{datetime.now().strftime('%Y')}` and your username written on it. 
- **__After verification please remove your ID.__**
- After staff verifies your date of birth, the bot will remove all traces of your ID from its system.

**__We may retain your blacked out ID for a maximum of 7 days for the server to complete this verification. Your ID is strictly used for verification purposes only__**

If you verify successfully, you will be granted access to the server and you will not need to ID again for any servers using AgeVerifier.
"""
	)
