import discord
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands

from classes.access import AccessControl
from classes.config.utils import ConfigUtils
from classes.support.queue import Queue
from databases.transactions.ConfigData import ConfigData
from databases.transactions.ConfigTransactions import ConfigTransactions
from resources.data.config_variables import DEFAULT_QUARANTINE_HOURS, FAIL_ACTION, JoinRequirementsToggles, \
	MAX_QUARANTINE_HOURS, QUARANTINE_HOURS_KEY, QUARANTINE_ROLE_KEY


class JoinGuard(commands.GroupCog, name="joinguard",
                description="Manage gatekeeping settings and verification requirements for joining members.") :
	"""
	Commands for configuring security parameters for new users joining the server.
	Requires 'Manage Server' permissions.
	"""

	def __init__(self, bot: commands.Bot) :
		self.bot = bot

	@app_commands.command(name="requirements", description="Enable or disable specific entry checks for joining members.")
	@app_commands.choices(
		requirement=[Choice(name=x.name.replace("_", " ").title(), value=x.value) for x in JoinRequirementsToggles],
		status=[Choice(name="Enabled", value="ENABLED"), Choice(name="Disabled", value="DISABLED")]
	)
	@app_commands.checks.has_permissions(manage_guild=True)
	@AccessControl().check_premium()
	async def requirements(self, interaction: discord.Interaction, requirement: Choice[str], status: Choice[str]) :
		"""
		Toggle individual join requirements like account age, avatar presence, or bot status.

		**Permissions:**
		- Requires `Manage Server` permission.
		"""
		await interaction.response.defer(ephemeral=True)

		ConfigTransactions().toggle(interaction.guild.id, requirement.value, status.value)

		Queue().add(
			ConfigUtils.log_change(
				interaction.guild,
				{requirement.value : status.value},
				user_name=interaction.user.mention
			)
		)

		readable_req = requirement.name
		await interaction.followup.send(
			f"Join Requirement Updated: **{readable_req}** has been set to **{status.name}**.",
			ephemeral=True
		)

	@app_commands.command(name="action",
	                      description="Configure the disciplinary action taken when a user fails join requirements.")
	@app_commands.choices(
		penalty=[
			Choice(name="Log Only", value="LOG"),
			Choice(name="Kick Member", value="KICK"),
			Choice(name="Quarantine Role", value="QUARANTINE"),
		]
	)
	@app_commands.checks.has_permissions(manage_guild=True)
	@AccessControl().check_premium()
	async def action(self, interaction: discord.Interaction, penalty: Choice[str]) :
		"""
		Define what the bot does when an incoming user flags one of your enabled requirements.
		Quarantine Role gives them the role set with `/joinguard quarantine` for a set time instead of kicking them.

		**Permissions:**
		- Requires `Manage Server` permission.
		"""
		await interaction.response.defer(ephemeral=True)

		ConfigTransactions().config_unique_add(
			guildid=interaction.guild.id,
			key=FAIL_ACTION,
			value=penalty.value,
			overwrite=True
		)

		Queue().add(
			ConfigUtils.log_change(
				interaction.guild,
				{FAIL_ACTION : penalty.value},
				user_name=interaction.user.mention
			)
		)

		message = f"Enforcement Action Updated: Members failing join checks will now trigger: **{penalty.name}**."
		if penalty.value == "QUARANTINE" and not ConfigData().get_channel_id(interaction.guild.id, QUARANTINE_ROLE_KEY) :
			message += "\nNo quarantine role is set yet, so failures are only logged until you set one with `/joinguard quarantine`."
		await interaction.followup.send(message, ephemeral=True)

	@app_commands.command(name="quarantine",
	                      description="Set the role and duration used by the Quarantine Role action.")
	@app_commands.checks.has_permissions(manage_guild=True)
	@AccessControl().check_premium()
	async def quarantine(self, interaction: discord.Interaction, role: discord.Role,
	                     hours: app_commands.Range[int, 1, MAX_QUARANTINE_HOURS] = DEFAULT_QUARANTINE_HOURS) :
		"""
		Set the role members get when they fail a join requirement and the action is Quarantine Role, and how many
		hours after joining it is taken off again (default 24, up to 720). Use a role only for this: anyone holding it
		longer than the duration since they joined has it removed.

		**Permissions:**
		- Requires `Manage Server` permission.
		"""
		await interaction.response.defer(ephemeral=True)

		if role.is_default() or role.managed :
			await interaction.followup.send("That role can't be given to members, pick another one.", ephemeral=True)
			return
		if role >= interaction.guild.me.top_role :
			await interaction.followup.send(
				f"{role.mention} is above my highest role, so I can't give it out. Move my role above it first.",
				ephemeral=True)
			return

		changes = {QUARANTINE_ROLE_KEY : role.id, QUARANTINE_HOURS_KEY : hours}
		for key, value in changes.items() :
			ConfigTransactions().config_unique_add(guildid=interaction.guild.id, key=key, value=value, overwrite=True)

		Queue().add(ConfigUtils.log_change(interaction.guild, changes, user_name=interaction.user.mention))

		await interaction.followup.send(
			f"Quarantine Updated: members who fail a join requirement get {role.mention} for **{hours} hour(s)**. "
			f"This is used when the action is set to Quarantine Role with `/joinguard action`.",
			ephemeral=True
		)

	@app_commands.command(name="minimum_age",
	                      description="Set the minimum required account age in days for joining members.")
	@app_commands.checks.has_permissions(manage_guild=True)
	@AccessControl().check_premium()
	async def minimum_age(self, interaction: discord.Interaction, days: int = 7) :
		"""
		Set the minimum age threshold (in days) an account must have to clear the ACCOUNT_AGE check.
		Default: 7
		**Permissions:**
		- Requires `Manage Server` permission.
		"""
		await interaction.response.defer(ephemeral=True)
	
		if days < 0 :
			await interaction.followup.send("The number of days cannot be negative.", ephemeral=True)
			return
	
		ConfigTransactions().config_unique_add(
			guildid=interaction.guild.id,
			key="MINIMUM_ACCOUNT_AGE",
			value=days,
			overwrite=True
		)
	
		Queue().add(
			ConfigUtils.log_change(
				interaction.guild,
				{"MINIMUM_ACCOUNT_AGE" : days},
				user_name=interaction.user.mention
			)
		)
	
		await interaction.followup.send(
			f"Minimum Account Age Updated: New members must have an account age of at least **{days} day(s)**.",
			ephemeral=True
		)


async def setup(bot: commands.Bot) :
	"""Adds the JoinGuard cog to the bot"""
	await bot.add_cog(JoinGuard(bot))
