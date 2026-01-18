import discord
from discord_py_utilities.messages import send_message

from classes.support.queue import Queue
from views.v2.OnboardingLayout import OnboardingLayout


class Onboarding :
	"""This module handles onboarding new servers, helping them get started with the bot."""

	async def join_message(self, channel: discord.TextChannel | discord.Member) :
		Queue().add(send_message(channel,
		                         f" ", view=OnboardingLayout()))
