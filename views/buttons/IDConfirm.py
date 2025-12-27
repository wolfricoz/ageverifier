import logging

import discord
from discord_py_utilities.messages import send_message, send_response

from classes.idcheck import IdCheck
from classes.idverify import verify
from classes.support.queue import Queue
from databases.transactions.VerificationTransactions import VerificationTransactions


class IDConfirm(discord.ui.View) :
	def __init__(self, dob: str, user: discord.Member | discord.User, ogmessage: discord.Message) :
		super().__init__(timeout=None)
		self.dateofbirth = dob
		self.user = user
		self.ogmessage = ogmessage

	@discord.ui.button(label="Confirm & Proceed", style=discord.ButtonStyle.green, custom_id="confirmID")
	async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button) :
		"""This is a button"""

		idcheck = VerificationTransactions().get_id_info(self.user.id)
		await verify(self.user, interaction, self.dateofbirth, True)
		if idcheck.idmessage:
			try :

				await IdCheck.remove_idmessage(self.user, idcheck)

			except (discord.NotFound, discord.Forbidden) as e :
				logging.info(f"Could not delete previous ID message for {self.user.id}: {e}")

		Queue().add(self.ogmessage.delete())
		await send_response(interaction, "User's ID verification entry has been updated.", ephemeral=True)
		await self.user.send(f"Your ID verification entry has been updated with the date of birth: {self.dateofbirth} and your ID has been removed from our system. Thank you for using AgeVerifier!")
		return None

	@discord.ui.button(label="Cancel Verification", style=discord.ButtonStyle.red, custom_id="declineID")
	async def decline(self, interaction: discord.Interaction, button: discord.ui.Button) :
		"""This is a button"""
		await send_response(interaction, "ID verification process has been cancelled. Thank you for double checking.", ephemeral=True)
		return None

	async def disable_buttons(self, interaction: discord.Interaction) :
		for item in self.children :
			item.disabled = True
		try :
			await interaction.message.edit(view=self)
		except Exception :
			pass

