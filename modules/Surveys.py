import logging

import discord
from discord.ext.commands import Cog, GroupCog, Bot

from classes.access import AccessControl
from databases.transactions.ConfigData import ConfigData
from views.buttons.SurveyButton import SurveyButton


class Surveys(GroupCog) :

	def __init__(self, bot: Bot) :
		self.bot = bot
		self.bot.add_view(SurveyButton())

	@Cog.listener(name='on_member_remove')
	async def on_member_remove(self, member) :
		"""This event handler sends the survey to the user when they leave the server."""
		if not ConfigData().get_toggle(member.guild.id, "SURVEY") or not AccessControl().is_premium(member.guild.id):
			return
		logging.info(f"sending survey to {member} for leaving {member.guild.name}")
		try :
			embed = discord.Embed(
				title=f"Feedback Survey for {member.guild.name}",
				description=f"Hi! We noticed you left the server. We'd love to hear your feedback on why you decided to leave! Please take a moment to fill out the survey by clicking the button below; it will help us improve our community.",
				color=discord.Color.blue()
			).set_footer(text=member.guild.id)
			await member.send(
				f"-# GDPR AND INFORMATION USE DISCLOSURE: By participating in this survey, you consent to having your responses stored by {member.guild.name} and used to improve our community. Your feedback will be kept confidential and will not be shared with third parties. Your username will be shared with the server administrators.",
				embed=embed,
				view = SurveyButton()
			)
		except discord.Forbidden:
			logging.warning(f"Could not send survey to {member} for leaving {member.guild.name}: We dont share a server.")
			pass

		except Exception as e:
			logging.warning(f"Could not send survey to {member} for leaving {member.guild.name}: {e}")
			pass

async def setup(bot: Bot) :
	await bot.add_cog(
		Surveys(bot),
	)
