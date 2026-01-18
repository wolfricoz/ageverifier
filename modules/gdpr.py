"""Checks the users invite info when they join and logs it"""
import os

import discord
from discord import app_commands
from discord.ext import commands
from discord_py_utilities.messages import send_response

from classes.encryption import Encryption
from databases.transactions.UserTransactions import UserTransactions
from databases.transactions.VerificationTransactions import VerificationTransactions
from views.buttons.gdprremoval import GDPRRemoval


class gdpr(commands.GroupCog, description="Commands related to your data and privacy.") :
	"""
	Commands related to your data and privacy.
	Here you can request a copy of your data or ask for it to be removed, in compliance with GDPR.
	These commands are available to all users.
	"""
	def __init__(self, bot: commands.Bot) :
		self.bot = bot

	@app_commands.command(name="removal", description="Request removal of your data")
	async def removal(self, interaction: discord.Interaction) :
		"""
		Starts the process to have your personal data removed from our database.
		When you use this command, we'll walk you through the next steps. Your data will be marked for deletion and permanently removed after a 30-day grace period.
		This action is in accordance with your rights under GDPR.

		Verifying your age will cancel the removal process, abuse of this feature may result in blacklisting.

		**Permissions:**
		- No special permissions are needed. This command can be used by anyone to manage their own data.
		"""
		user = UserTransactions().get_user(interaction.user.id)
		if user is None or user.date_of_birth is None :
			await send_response(interaction, "No data found for you.")
			return
		dev_channel = self.bot.get_channel(int(os.getenv("DEV")))
		# await send_message(dev_channel, f"{interaction.user.mention} has requested to have their data removed, data has been marked for removal in 30 days.")
		text = """You have requested to have your data removed under GDPR. 

- AgeVerifier cannot confirm your age, so we will notify the owners of any guilds you are in.  
- Your data will be **hidden for 30 days** before being permanently deleted.  
- If you submit your date of birth again during this time, the removal process will be **canceled**.  

If you want to continue, please confirm your request."""

		await send_response(interaction, text, view=GDPRRemoval(), ephemeral=True)

	@app_commands.command(name="data", description="Request your data")
	async def data(self, interaction: discord.Interaction) :
		"""
		Use this command to request a copy of all the personal data we have stored about you.
		For your privacy and security, the bot will send this information directly to your DMs.

		**Permissions:**
		- No special permissions are needed. This command can be used by anyone to request their own data.
		"""
		dev = os.getenv('DEV')
		supportguild = os.getenv("SUPPORTGUILD")
		user_data = UserTransactions().get_user(interaction.user.id)
		id_verified = VerificationTransactions().get_id_info(interaction.user.id)
		server = self.bot.get_guild(int(supportguild if supportguild else 0))
		if server is None :
			invite = "Failed to generate invite link, please contact the developer."
		else :
			invite = await server.get_channel(int(dev if dev else 0)).create_invite(max_age=3600, max_uses=1,
			                                                                  reason="GDPR data request")
		if user_data is None :
			await interaction.user.send(f"**__User Data Request__**"
			                            f"\nUser: {interaction.user.mention}({interaction.user.id})"
			                            f"\n**No data found for you.**")
			return

		await interaction.user.send(f"**__User Data Request__**"
		                            f"\nUser: {interaction.user.mention}({interaction.user.id})"
		                            f"\ndate of birth (decrypted): {Encryption().decrypt(user_data.date_of_birth) if user_data.date_of_birth is not None else 'Not set'}"
		                            f"\nLast server: {user_data.server if user_data.server is not None else 'Not set'}"
		                            f"\nID Verificatied: {'Yes' if id_verified and id_verified.idverified else 'No'}"
		                            f"\n\n-# Note: All personal data is encrypted and stored securely. If you have any questions or concerns please contact the developer `ricostryker` or join our [support server]({invite}) and open a ticket.")

		await send_response(interaction, "Your data will be sent to you through DM..", ephemeral=True)


async def setup(bot) :
	"""Adds cog to the bot"""
	await bot.add_cog(gdpr(bot))
