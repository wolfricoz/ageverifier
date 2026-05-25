import discord
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands

from classes.access import AccessControl
from classes.config.utils import ConfigUtils
from classes.support.queue import Queue
from databases.transactions.ConfigTransactions import ConfigTransactions
from resources.data.config_variables import FAIL_ACTION, JoinRequirementsToggles


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
		]
	)
	@app_commands.checks.has_permissions(manage_guild=True)
	@AccessControl().check_premium()
	async def action(self, interaction: discord.Interaction, penalty: Choice[str]) :
		"""
		Define what the bot does when an incoming user flags one of your enabled requirements.

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

		await interaction.followup.send(
			f"Enforcement Action Updated: Members failing join checks will now trigger: **{penalty.name}**.",
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
