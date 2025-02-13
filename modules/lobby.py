"""this module handles the lobby."""
import datetime
import os

import discord
from discord import app_commands
from discord.ext import commands

import classes.permissions as permissions
from classes.AgeCalculations import AgeCalculations
from classes.databaseController import ConfigData
from classes.idverify import verify
from classes.lobbyprocess import LobbyProcess
from classes.support.discord_tools import send_response
from classes.whitelist import check_whitelist
from views.buttons.approvalbuttons import ApprovalButtons
from views.buttons.confirmButtons import confirmAction
from views.buttons.dobentrybutton import dobentry
from views.buttons.verifybutton import VerifyButton


class Lobby(commands.GroupCog) :
	def __init__(self, bot: commands.Bot) :
		self.bot = bot
		self.index = 0
		self.bot.add_view(VerifyButton())
		self.bot.add_view(ApprovalButtons())
		self.bot.add_view(dobentry())

	@app_commands.command(name="button")
	@app_commands.checks.has_permissions(administrator=True)
	async def verify_button(self, interaction: discord.Interaction, text: str) :
		"""Verification button for the lobby; initiates the whole process"""
		await interaction.channel.send(text, view=VerifyButton())

	@app_commands.command()
	@app_commands.checks.has_permissions(administrator=True)
	async def idverify(self, interaction: discord.Interaction, process: bool,
	                   user: discord.User, dob: str) :
		"""ID verifies user. process True will put the user through the lobby."""
		if check_whitelist(interaction.guild.id) is False and not permissions.check_dev(interaction.user.id) :
			await send_response(interaction,
			                    "[NOT_WHITELISTED] This command is limited to whitelisted servers. Please contact the developer `ricostryker` to verify the user.")
			return
		try :
			await interaction.response.defer(ephemeral=True)
		except discord.InteractionResponded :
			pass
		await AgeCalculations.validatedob(dob, interaction)
		await verify(user, interaction, dob, process)

	@app_commands.command()
	@app_commands.checks.has_permissions(manage_messages=True)
	async def returnlobby(self, interaction: discord.Interaction, user: discord.Member) :
		"""returns user to lobby; removes the roles."""
		await interaction.response.defer()
		add_roles: list = ConfigData().get_key(interaction.guild.id, "add")
		add = list(add_roles)
		rem: list = ConfigData().get_key(interaction.guild.id, "rem")
		returns: list = ConfigData().get_key(interaction.guild.id, "return")
		print('data retrieved')
		rm = []
		ra = []
		for role in rem :
			r = interaction.guild.get_role(role)
			ra.append(r)
		for role in add + returns :
			r = interaction.guild.get_role(role)
			rm.append(r)
		print('roles retrieved')
		await user.remove_roles(*rm, reason="returning to lobby")
		await user.add_roles(*ra, reason="returning to lobby")
		print('roles changed')
		await interaction.followup.send(
			f"{user.mention} has been moved back to the lobby by {interaction.user.mention}")

	@app_commands.command()
	@app_commands.checks.has_permissions(manage_messages=True)
	async def agecheck(self, interaction: discord.Interaction, dob: str) :
		"""Checks the age of a dob"""
		age = AgeCalculations.dob_to_age(dob)
		await interaction.response.send_message(f"As of today {dob} is {age} years old", ephemeral=True)

	@commands.command(name="approve")
	@commands.has_permissions(manage_messages=True)
	async def approve(self, ctx: commands.Context, user: discord.Member, age: int, dob: str) :
		"""allows user to enter"""
		dob = AgeCalculations.regex(dob)
		await LobbyProcess.approve_user(ctx.guild, user, dob, age, ctx.author.name)
		await ctx.message.delete()

	@app_commands.command()
	@app_commands.checks.has_permissions(administrator=True)
	async def purge(self, interaction: discord.Interaction, days: int = 14) :
		"""This command will kick all the users that have not been processed through the lobby with the given days."""
		lobby_config = ConfigData().get_key_int(interaction.guild.id, "lobby")
		lobby_channel = interaction.guild.get_channel(lobby_config)
		if days > 14 :
			days = 14
			await interaction.channel.send("Max days is 14, setting to 14")

		view = confirmAction()
		await view.send_message(interaction,
		                        f"Are you sure you want to purge the lobby of users that have not been processed in the last {days} days?")
		await view.wait()
		if view.confirmed is False :
			await interaction.followup.send("Purge cancelled")
			return
		days_to_datetime = datetime.datetime.now() - datetime.timedelta(days=days)
		kicked = []
		async for x in lobby_channel.history(limit=None, after=days_to_datetime) :
			if x.author.bot is False :
				continue
			for a in x.mentions :
				try :
					await a.kick()
					kicked.append(f"{a.name}({a.id})")
				except Exception as e :
					print(f"unable to kick {a} because {e}")
			await x.delete()
		with open("config/kicked.txt", "w") as file :
			str_kicked = "\n".join(kicked)
			file.write(f"these users were removed during the purge:\n")
			file.write(str_kicked)
		await interaction.channel.send(f"{interaction.user.mention} Kicked {len(kicked)}",
		                               file=discord.File(file.name, "kicked.txt"))
		os.remove("config/kicked.txt")


async def setup(bot) :
	"""Adds the cog to the bot."""
	await bot.add_cog(Lobby(bot))
