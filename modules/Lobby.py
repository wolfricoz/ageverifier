"""this module handles the lobby."""
import datetime
import io
import logging

import discord
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands
from discord_py_utilities.messages import send_response
from discord_py_utilities.permissions import check_missing_channel_permissions, check_missing_guild_permissions

import classes.permissions as permissions
from classes.AgeCalculations import AgeCalculations
from classes.config.utils import is_unset
from classes.idverify import verify
from classes.lobby.Clean import clean_lobby
from classes.lobbyprocess import LobbyProcess
from classes.permissions_notice import PermissionNotice
from classes.text import plural
from classes.whitelist import check_whitelist
from databases.transactions.ConfigData import ConfigData
from views.buttons.approvalbuttons import ApprovalButtons
from views.buttons.confirmButtons import confirmAction
from views.buttons.dobentrybutton import dobentry
from views.buttons.verifybutton import GDPR_DISCLOSURE, VerifyButton

MAX_RAID_PURGE_DAYS = 30


def configured_roles(guild: discord.Guild, key: str) -> list[discord.Role] :
	"""The roles stored under a config key. Unset keys and deleted roles are skipped: a deleted role used to reach
	remove_roles() as None and crash /lobby returnlobby."""
	value = ConfigData().get_key_or_none(guild.id, key)
	if is_unset(value) :
		return []
	# The age roles (VERIFICATION_ADD_ROLE) are cached as {role_id: {"MAX": .., "MIN": ..}}; the ids are the keys.
	role_ids = list(value) if isinstance(value, (list, dict)) else [value]
	roles = []
	for role_id in role_ids :
		try :
			role = guild.get_role(int(role_id))
		except (TypeError, ValueError) :
			role = None
		if role is not None :
			roles.append(role)
	return roles


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
			f"{text}\n{GDPR_DISCLOSURE}",
			view=VerifyButton(interaction.guild.id))
		# Without a response Discord shows "The application did not respond", even though the button was posted.
		await send_response(interaction, "The verification button has been posted in this channel.", ephemeral=True)

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
		dob = await AgeCalculations.validatedob(dob, interaction)
		if dob is False :
			return
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
		guild = interaction.guild
		# Undo verification: take the verified roles (and return_remove_role) off, give back the roles verification removed.
		remove = [role for role in configured_roles(guild, "verification_add_role") + configured_roles(guild, "return_remove_role")
		          if role in user.roles]
		add = [role for role in configured_roles(guild, "verification_remove_role") if role not in user.roles]
		if not remove and not add :
			return await interaction.followup.send(
				f"{user.mention} has none of the verified roles and already has the lobby roles, so there was nothing to change. "
				"The roles come from `verification_add_role`, `verification_remove_role` and `return_remove_role` in `/config roles`.",
				ephemeral=True)
		try :
			if remove :
				await user.remove_roles(*remove, reason="returning to lobby")
			if add :
				await user.add_roles(*add, reason="returning to lobby")
		except discord.Forbidden :
			return await PermissionNotice.respond(interaction, missing=["manage_roles"],
			                                      purpose=f"move {user.name} back to the lobby")
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
		dob = await AgeCalculations.validatedob(dob, interaction)
		if dob is False :
			# validatedob has already told the user which format to use.
			return
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
	@app_commands.describe(days="How many days back to look (at most 30)",
	                       dry_run="Only list who would be kicked, without kicking anyone")
	async def raid_purge(self, interaction: discord.Interaction, days: int = 30, dry_run: bool = False) :
		"""
        Kicks all users who joined during a suspected raid.
        This command looks at the join messages in the lobby channel within a specified number of days and kicks all mentioned users.
        You will be shown how many members would be kicked, and asked for confirmation before the purge begins. Use `dry_run` to only see the list.

        **Permissions:**
        - You'll need `Administrator` permission to use this command.
        """
		lobby_config = ConfigData().get_key_int(interaction.guild.id, "server_join_channel")
		lobby_channel = interaction.guild.get_channel_or_thread(lobby_config)
		days = max(1, min(days, MAX_RAID_PURGE_DAYS))

		if lobby_channel is None :
			await send_response(interaction, "The lobby channel no longer exists. Set a new one with `/config channels`.", ephemeral=True)
			return
		# Every kick and delete below would fail one by one with nothing shown, so stop before asking for confirmation.
		# A dry run only reads the lobby.
		needed_in_lobby = ["view_channel", "read_message_history"] + ([] if dry_run else ["manage_messages"])
		missing_in_lobby = check_missing_channel_permissions(lobby_channel, needed_in_lobby)
		missing = ([] if dry_run else check_missing_guild_permissions(interaction.guild, ["kick_members"])) + missing_in_lobby
		if missing :
			await PermissionNotice.respond(interaction, missing=missing, channel=lobby_channel if missing_in_lobby else None,
			                               purpose="purge the lobby")
			return

		cutoff = datetime.datetime.now() - datetime.timedelta(days=days)
		join_messages, members = [], {}
		async for message in lobby_channel.history(limit=None, after=cutoff) :
			if not message.author.bot :
				continue
			join_messages.append(message)
			for member in message.mentions :
				# Members who already left can't be kicked again.
				if isinstance(member, discord.Member) :
					members[member.id] = member
		period = f"the last {plural(days, 'day')}"
		if not members :
			await send_response(interaction, f"Nobody who joined in {period} is still in the lobby, so there is nothing to purge.",
			                    ephemeral=True)
			return
		names = ", ".join(member.name for member in list(members.values())[:20])
		if len(members) > 20 :
			names += f" and {len(members) - 20} more"
		if dry_run :
			await send_response(interaction, f"Dry run: a purge would kick {plural(len(members), 'member')} who joined in {period}: {names}.\n"
			                                 f"Run it without `dry_run` to kick them.", ephemeral=True)
			return

		view = confirmAction()
		await view.send_message(interaction, f"This kicks **{plural(len(members), 'member')}** who joined in {period} and deletes "
		                                     f"their join messages: {names}.\nAre you sure?")
		await view.wait()
		if not view.confirmed :
			await interaction.followup.send("Purge cancelled", ephemeral=True)
			return
		kicked, failed = [], []
		for member in members.values() :
			try :
				await member.kick(reason=f"Raid purge by {interaction.user.name}")
				kicked.append(f"{member.name}({member.id})")
			except discord.HTTPException as e :
				logging.info(f"Raid purge could not kick {member.id} in {interaction.guild.id}: {e}")
				failed.append(f"{member.name}({member.id})")
		for message in join_messages :
			try :
				await message.delete()
			except discord.HTTPException :
				pass
		report = "These users were removed during the purge:\n" + "\n".join(kicked)
		if failed :
			# Usually a role at or above the bot's; the member stays in the server.
			report += "\n\nThese users could not be kicked (their role is probably above the bot's):\n" + "\n".join(failed)
		await interaction.followup.send(f"{interaction.user.mention} Kicked {plural(len(kicked), 'member')}"
		                                + (f", {len(failed)} could not be kicked" if failed else "") + ".",
		                                file=discord.File(io.BytesIO(report.encode("utf-8")), "kicked.txt"))

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
