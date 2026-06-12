"""this module handles the lobby."""
import datetime
import os

import discord
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands
from discord_py_utilities.messages import send_response

import classes.permissions as permissions
from classes.AgeCalculations import AgeCalculations
from classes.idverify import verify
from classes.lobby.Clean import clean_lobby
from classes.lobbyprocess import LobbyProcess
from classes.whitelist import check_whitelist
from databases.transactions.ConfigData import ConfigData
from views.buttons.approvalbuttons import ApprovalButtons
from views.buttons.confirmButtons import confirmAction
from views.buttons.dobentrybutton import dobentry
from views.buttons.verifybutton import VerifyButton


class Lobby(commands.GroupCog, description="Commands for managing the new member lobby and verification process.") :
	"""
	Commands for managing the new member lobby and verification process.
	This includes tools for manual verification, age checks, and purging inactive users from the lobby.
	"""

	def __init__(self, bot: commands.Bot) :
		self.bot = bot
		self.index = 0
		self.bot.add_view(VerifyButton())
		self.bot.add_view(ApprovalButtons())
		self.bot.add_view(dobentry())

	@app_commands.command(name="button", description="Creates the main verification button in your lobby channel.")
	@app_commands.checks.has_permissions(administrator=True)
	async def verify_button(self, interaction: discord.Interaction, text: str) :
		"""
        Creates the main verification button in your lobby channel.
        When new users click this button, it kicks off the entire age verification process. You can customize the message that appears above the button.

        **Permissions:**
        - You'll need `Administrator` permission to use this command.
        """
		await interaction.channel.send(
			f"{text}\n-# GDPR AND INFORMATION USE DISCLOSURE: By entering your birth date (MM/DD/YYYY) and age, you consent to having this information about you stored by Age Verifier and used to verify that you are the age that you say you are, including sharing to relevant parties for age verification. This information will be stored for a maximum of 1 year if you are no longer in a server using Ageverifier.",
			view=VerifyButton())

	@app_commands.command(description="Manually verifies a user with their ID and date of birth.")
	@app_commands.checks.has_permissions(administrator=True)
	async def idverify(self, interaction: discord.Interaction, process: bool,
	                   user: discord.Member, dob: str) :
		"""
        Manually verifies a user with their ID and date of birth.
        This is a powerful tool for whitelisted servers to bypass the standard flow for trusted users.
        You can choose whether to put them through the full lobby process or just verify them instantly.

        **Permissions:**
        - You'll need `Administrator` permission.
        - Your server must be whitelisted to use this command.
        """

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

	@app_commands.command(description="Moves a user who has already been verified back into the lobby.")
	@app_commands.checks.has_permissions(manage_messages=True)
	@app_commands.guild_only()
	async def returnlobby(self, interaction: discord.Interaction, user: discord.Member) :
		"""
        Moves a user who has already been verified back into the lobby.
        This command will remove their verified roles and re-assign the unverified roles, effectively resetting their verification status on this server.

        **Permissions:**
        - You'll need the `Manage Messages` permission to use this command.
        """
		await interaction.response.defer()
		if interaction.guild is None :
			return await send_response(interaction, "This command is limited to a server.")
		add_roles: list = ConfigData().get_key(interaction.guild.id, "VERIFICATION_ADD_ROLE")
		add = list(add_roles)
		rem: list = ConfigData().get_key(interaction.guild.id, "verification_remove_role")
		returns: list = ConfigData().get_key(interaction.guild.id, "return_remove_role")
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
		return await interaction.followup.send(
			f"{user.mention} has been moved back to the lobby by {interaction.user.mention}")

	@app_commands.command(description="Quickly calculates the age based on a given date of birth.")
	@app_commands.checks.has_permissions(manage_messages=True)
	async def agecheck(self, interaction: discord.Interaction, dob: str) :
		"""
        Quickly calculates the age based on a given date of birth.
        This is a simple utility to check how old someone is without going through the full verification process.

        **Permissions:**
        - You'll need the `Manage Messages` permission to use this command.
        """
		await AgeCalculations.validatedob(dob, interaction)
		age = AgeCalculations.dob_to_age(dob)
		await send_response(interaction, f"As of today {dob} is {age} years old", ephemeral=True)

	@commands.command(name="approve")
	@commands.has_permissions(manage_messages=True)
	async def approve(self, ctx: commands.Context, user: discord.Member, age: int, dob: str) :
		"""
        Manually approves a user and grants them access to the server.
        This is a prefix command used by moderators to approve a user after a manual review. It logs the approval and assigns the correct roles.

        **Permissions:**
        - You'll need the `Manage Messages` permission to use this command.
        """
		dob = AgeCalculations.dob_regex(dob)
		await LobbyProcess.approve_user(ctx.guild, user, dob, age, ctx.author.name)
		await ctx.message.delete()

	@app_commands.command(description="Kicks all users who joined during a suspected raid.")
	@app_commands.checks.has_permissions(administrator=True)
	async def raid_purge(self, interaction: discord.Interaction, days: int = 30) :
		"""
        Kicks all users who joined during a suspected raid.
        This command looks at the join messages in the lobby channel within a specified number of days and kicks all mentioned users.
        You will be asked for confirmation before the purge begins.

        **Permissions:**
        - You'll need `Administrator` permission to use this command.
        """
		lobby_config = ConfigData().get_key_int(interaction.guild.id, "server_join_channel")
		lobby_channel = interaction.guild.get_channel(lobby_config)
		if days > 30 :
			days = 30
			await interaction.channel.send("Max days is 14, setting to 14")

		view = confirmAction()
		await view.send_message(interaction,
		                        f"Are you sure you want to purge the lobby of users that have not been processed in the last {days} days?")
		await view.wait()
		if not view.confirmed :
			await interaction.followup.send("Purge cancelled")
			return
		days_to_datetime = datetime.datetime.now() - datetime.timedelta(days=days)
		kicked = []
		async for x in lobby_channel.history(limit=None, after=days_to_datetime) :
			if not x.author.bot :
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

	@app_commands.command(description="Kicks users who have been waiting in the lobby for too long.")
	@app_commands.checks.has_permissions(administrator=True)
	@app_commands.choices(
		mode=[
			Choice(name="Dry Run", value="dry"),
			Choice(name="Clean Only", value="clean"),
			Choice(name="Kick Only", value="kick"),
			Choice(name="Kick & Clean", value="full"),
		]
	)
	async def lobby_purge(self, interaction: discord.Interaction, mode: Choice[str], days: int = 30) :
		"""
			Kicks users who have been waiting in the lobby for too long by checking the age of their welcome messages. If a message is older than the specified number of days, the user will be kicked to keep the lobby clean.

      **Queue Notice:** Actions are queued and may take 10 minutes to 24 hours to complete depending on message volume.

      **Modes:**
      * **Dry Run (`dry`):** Logs what would happen without kicking users or deleting messages.
      * **Clean Only (`clean`):** Deletes the welcome messages and messages of users who have left but keeps the users.
      * **Kick Only (`kick`):** Kicks the users but leaves their welcome messages.
      * **Kick & Clean (`full`):** Kicks the users and deletes their welcome messages.

      **Permissions:**
      - You'll need `Administrator` permission to use this command.
        """

		# Define the variables
		kick = False
		clean = False

		# change the variables based on the chosen mode
		match mode.value.lower() :
			case "clean" :
				clean = True
			case "kick" :
				kick = True
			case "full" :
				kick = True
				clean = True
			case _ :
				# It's always defaulting to dry unless something else is chosen, this way we don't accidentally kick.
				pass
		if days > 30 :
			days = 30
			await interaction.channel.send("Max days is 30, setting to 30")
		view = confirmAction()
		await view.send_message(
			interaction,
			f"Are you sure you want to kick users who have been inactive in the lobby for more than {days} days based on the server_join_message? This action will also clean up all messages from users who have left the server_join_channel. {'Running in dry mode, no users will be kicked or messages will be removed.' if not kick and not clean else ''}"
		)
		await view.wait()
		if not view.confirmed :
			await interaction.followup.send("Purge cancelled")
			return
		await clean_lobby(self.bot, interaction.guild, days, clean=clean, kick=kick)


async def setup(bot) :
	"""Adds the cog to the bot."""
	await bot.add_cog(Lobby(bot))
