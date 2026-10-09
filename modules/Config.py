"""Config options for the bot."""
import asyncio
import datetime
import json
import logging
import os

import discord
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands
from discord_py_utilities.messages import send_message, send_response
from discord_py_utilities.permissions import check_missing_channel_permissions

from classes.access import AccessControl
from classes.config.utils import ConfigUtils
from classes.configsetup import ConfigSetup
from classes.support.queue import Queue
from databases.transactions.AgeRoleTransactions import AgeRoleTransactions
from databases.transactions.ConfigData import ConfigData
from databases.transactions.ConfigTransactions import ConfigTransactions
from resources.data.config_variables import MAX_BUTTON_LABEL_LENGTH, MAX_VERIFICATION_REMINDER_MINUTES, \
	PREMIUM_VERIFICATION_METHODS, REVERIFICATION_KEY, \
	VERIFICATION_KEY, VERIFICATION_REMINDER_KEY, \
	VerificationMethods, \
	available_toggles, channelchoices, \
	lobby_approval_toggles, messagechoices, \
	rolechoices
from views.modals.configinput import ConfigInputUnique
from views.v2.HelpLayout import HelpLayout


class Config(commands.GroupCog, name="config",
             description="Commands for configuring the bot's settings in the server.") :
	"""
	Commands for configuring the bot's settings in the server.
	This includes setting up channels, roles, custom messages, and feature toggles.
	Most commands require 'Manage Server' permissions.
	"""

	def __init__(self, bot: commands.Bot) :
		self.bot = bot

	rolechoices = rolechoices
	channelchoices = channelchoices
	messagechoices = messagechoices
	available_toggles = available_toggles

	@app_commands.command(name="help", description="Are you stuck? This command will help you.")
	async def help(self, interaction: discord.Interaction) :
		"""
				If you're feeling stuck or need assistance with configuring the bot, this command will provide you with helpful information and guidance.

		"""
		await send_response(interaction, " ", view=HelpLayout())

	@app_commands.command(name='setup', description="Helps you get the bot set up on your server.")
	@app_commands.checks.has_permissions(manage_guild=True)
	@app_commands.choices(setup_type=[Choice(name=x, value=x) for x in ['dashboard', 'manual', 'auto']])
	async def configsetup(self, interaction: discord.Interaction, setup_type: Choice[str]) :
		"""
        This command helps you get the bot set up on your server. You have a few options to choose from:
        'dashboard' will give you a link to our web dashboard for an easy, graphical setup experience.
        'manual' will guide you step-by-step through the setup process using Discord commands.
        'auto' will automatically create the necessary roles and channels to get the bot running quickly.

        **Permissions:**
        - You'll need the `Manage Server` permission to use this command.
        - The bot needs `Send Messages`, `Embed Links`, and `View Channel` permissions in the channel where you run this command.
        """
		if check_missing_channel_permissions(interaction.channel, ['send_messages', 'embed_links', 'view_channel']) :
			return await send_response(interaction,
			                           "I do not have permission to send messages or embed links in this channel. Please fix this and try again.",
			                           ephemeral=True)
		await send_message(interaction.channel,
		                   "For more information about setting up the bot, visit our [Documentation](<https://wolfricoz.github.io/ageverifier/commands/Config.html>)")
		logging.info(f"{interaction.guild.name} started {setup_type.value}")
		status: bool = True
		match setup_type.value.lower() :
			case 'dashboard' :
				return await send_response(interaction, f"You can access the dashboard here: {os.getenv("dashboard_url")}")
			case 'manual' :
				await send_message(interaction.channel,
				                   f"You can access the dashboard here for easier setup! {os.getenv("DASHBOARD_URL")}")
				status = await ConfigSetup().manual(self.bot, interaction, self.channelchoices, self.rolechoices,
				                                    self.messagechoices)
			case 'auto' :
				status = await ConfigSetup().auto(interaction, self.channelchoices, self.rolechoices, self.messagechoices)

		if not status :
			# Cancelled or timed out; the setup flow has already told the user.
			return None
		await send_response(interaction,
		                    "The config has been successfully setup, if you wish to check our toggles you please do /config toggles. Permission checking will commence shortly.",
		                    ephemeral=True)
		await ConfigSetup().check_channel_permissions(interaction.guild)
		return None

	@app_commands.command(description="Triggers a check to ensure the bot has all the necessary permissions.")
	@app_commands.checks.has_permissions(manage_guild=True)
	async def permissioncheck(self, interaction: discord.Interaction) :
		"""
        This command triggers a check to ensure the bot has all the necessary permissions in the channels you've configured for it.
        It's a great way to diagnose problems if the bot isn't behaving as expected. Any issues found will be reported, usually in your log channel.

        **Permissions:**
        - You'll need the `Manage Server` permission to use this command.
        """
		await send_response(interaction, f"Starting to check permissions for all the channels!", ephemeral=True)
		await ConfigSetup().check_channel_permissions(interaction.guild)

	@app_commands.command(description="Lets you customize the various messages the bot sends.")
	@app_commands.choices(key=[Choice(name=x, value=x) for x, _ in messagechoices.items()])
	@app_commands.choices(action=[Choice(name=x, value=x) for x in ['set', 'Remove']])
	@app_commands.checks.has_permissions(manage_guild=True)
	async def messages(self, interaction: discord.Interaction, key: Choice[str], action: Choice[str]) :
		"""
        Lets you customize the various messages the bot sends. You can either set a new custom message or remove an existing one to revert it back to the default.
        When you choose to 'set' a message, a pop-up will appear for you to enter your new text.

        Some of these are premium only, such as `verification_button_label`, which changes the text on the verification button itself.

        **Permissions:**
        - You'll need the `Manage Server` permission to use this command.
        """
		match action.value.lower() :
			case 'set' :
				# Only setting is gated: a server whose premium lapsed can still clear a value
				# it set earlier, even though the bot already falls back to the default for it.
				if key.value == "verification_button_label" and not AccessControl().is_premium(interaction.guild.id) :
					return await send_response(interaction,
					                           f"`{key.value}` is a premium setting. Without premium the default is used instead. "
					                           f"You can find out more about premium here: {os.getenv('DASHBOARD_URL')}",
					                           ephemeral=True)
				# Button labels have a much lower ceiling than a normal message; the modal is
				# capped so an over-long label can never reach Discord in the first place.
				max_length = MAX_BUTTON_LABEL_LENGTH if key.value == "verification_button_label" else 512
				# noinspection PyUnresolvedReferences
				await interaction.response.send_modal(ConfigInputUnique(key=key.value, max_length=max_length))

			case 'remove' :
				await interaction.response.defer(ephemeral=True)
				result = ConfigTransactions().config_unique_remove(guild_id=interaction.guild.id, key=key.value)
				if result is False :
					await interaction.followup.send(f"{key.value} was not in database")
					return
				Queue().add(
					ConfigUtils.log_change(interaction.guild, {key : None}, user_name=interaction.user.mention,
					                       ))
				await interaction.followup.send(f"{key.value} has been removed from the database", ephemeral=True)
			case _ :
				raise NotImplementedError

	@app_commands.command(description="Allows you to enable or disable various features of the bot.")
	@app_commands.choices(action=[Choice(name=x, value=x) for x in ["enabled", "disabled"]],
	                      key=[Choice(name=x, value=x) for x in available_toggles])
	@app_commands.checks.has_permissions(manage_guild=True)
	async def toggles(self, interaction: discord.Interaction, key: Choice[str], action: Choice[str]) :
		"""
        This command allows you to enable or disable various features of the bot.
        You can turn things on or off to best suit your server's needs.

        **Permissions:**
        - You'll need the `Manage Server` permission to use this command.
        """
		match action.value.upper() :
			case "ENABLED" :
				ConfigTransactions().toggle(interaction.guild.id, key.value, action.value.upper())

			case "DISABLED" :
				ConfigTransactions().toggle(interaction.guild.id, key.value, action.value.upper())
				if key.value == "send_join_message" :
					return send_response(interaction,
					                     f"The lobby welcome message has been disabled. Users will no longer receive a welcome message or the verification button in the lobby channel. To allow users to verify, please use the /lobby command in the channel.",
					                     ephemeral=True)
		Queue().add(
			ConfigUtils.log_change(interaction.guild, {key.value : action.value.upper()}, user_name=interaction.user.mention,
			                       ))
		return await send_response(interaction, f"{key.value} has been set to {action.value}", ephemeral=True)

	@app_commands.command(description="Customize the buttons that appear on the verification approval message.")
	@app_commands.choices(action=[Choice(name=x, value=x) for x in ["enabled", "disabled"]],
	                      key=[Choice(name=x, value=x) for x in lobby_approval_toggles])
	@app_commands.checks.has_permissions(manage_guild=True)
	async def approval_toggles(self, interaction: discord.Interaction, key: Choice[str], action: Choice[str]) :
		"""
        Use this command to customize the buttons that appear on the verification approval message in your log channel.
        This allows you to enable or disable specific actions your moderators can take, like banning or noting a user's ID.

        I highly recommend using the website, as it provides a more user-friendly interface for configuring these settings. You can see the changes in real-time and understand the impact of each toggle better.

        **Permissions:**
        - You'll need the `Manage Server` permission to use this command.
        """
		match action.value.upper() :
			case "ENABLED" :
				ConfigTransactions().toggle(interaction.guild.id, key.value, action.value.upper())
			case "DISABLED" :
				ConfigTransactions().toggle(interaction.guild.id, key.value, action.value.upper())
		Queue().add(
			ConfigUtils.log_change(interaction.guild, {key.value : action.value.upper()}, user_name=interaction.user.mention,
			                       ))
		return await send_response(interaction, f"{key.value} has been set to {action.value}", ephemeral=True)

	@app_commands.command(description="Assigning specific channels for the bot's functions.")
	@app_commands.choices(key=[Choice(name=f"{x} channel", value=x) for x, _ in channelchoices.items()])
	@app_commands.choices(action=[Choice(name=x, value=x) for x in ["set", "remove"]])
	@app_commands.checks.has_permissions(manage_guild=True)
	async def channels(self, interaction: discord.Interaction, key: Choice[str], action: Choice[str],
	                   value: discord.TextChannel = None) :
		"""
        This command is for assigning specific channels for the bot's functions, like a channel for logging or a lobby for new members.
        You can either 'set' a new channel or 'remove' an existing assignment.


        **Permissions:**
        - You'll need the `Manage Server` permission to use this command.
        """
		await interaction.response.defer(ephemeral=True)
		if value is not None :
			value = value.id
		match action.value.lower() :
			case 'set' :
				ConfigTransactions().config_unique_add(guildid=interaction.guild.id, key=key.value, value=value,
				                                       overwrite=True)
				Queue().add(ConfigUtils.log_change(interaction.guild, {key.value : value}, user_name=interaction.user.mention))
				await interaction.followup.send(f"{key.value} has been added to the database with value:\n{value}")
			case 'remove' :
				result = ConfigTransactions().config_unique_remove(guild_id=interaction.guild.id, key=key.value)
				if result is False :
					await interaction.followup.send(f"{key.value} was not in database")
					return
				Queue().add(ConfigUtils.log_change(interaction.guild, {key.value : None}, user_name=interaction.user.mention))
				await interaction.followup.send(f"{key.value} has been removed from the database")
			case _ :
				raise NotImplementedError

	@app_commands.command(description="Manage which roles the bot interacts with.")
	@app_commands.choices(key=[Choice(name=f"{ke} role", value=ke) for ke, val in rolechoices.items()])
	@app_commands.choices(action=[Choice(name=x, value=x) for x in ["add", 'remove']])
	@app_commands.checks.has_permissions(manage_guild=True)
	async def roles(self, interaction: discord.Interaction, key: Choice[str], action: Choice[str], value: discord.Role,
	                minimum_age: int = 18, maximum_age: int = 200) :
		"""
        Use this command to manage which roles the bot interacts with. You can configure roles to be assigned upon verification,
        including setting minimum and maximum age requirements for specific roles.


        **Permissions:**
        - You'll need the `Manage Server` permission to use this command.
        """
		await interaction.response.defer(ephemeral=True)
		value = value.id
		# The choice values are the lowercase rolechoices keys, while config keys are stored
		# uppercase; comparing key.value directly never matched, so age roles lost their ages.
		config_key = key.value.upper()
		match action.value.lower() :
			case "add" :
				if config_key == "VERIFICATION_ADD_ROLE" and maximum_age and minimum_age :
					AgeRoleTransactions().add(guild_id=interaction.guild.id, role_id=value, role_type=config_key,
					                          minimum_age=minimum_age, maximum_age=maximum_age)
					Queue().add(ConfigUtils.log_change(interaction.guild, {
						key.value : f"role id: {value} minimum_age: {minimum_age} maximum age: {maximum_age}"},
					                                   user_name=interaction.user.mention))

					await interaction.followup.send(f"{key.name}: <@&{value}> has been added to the database")
					return
				Queue().add(ConfigUtils.log_change(interaction.guild, {
					key.value : f"role id: {value} minimum_age: {minimum_age} maximum age: {maximum_age}"},
				                                   user_name=interaction.user.mention))
				result = ConfigTransactions().config_key_add(guildid=interaction.guild.id, key=key.value.upper(),
				                                             value=value, overwrite=False)
				if result is False :
					await interaction.followup.send(f"{key.name}: <@&{value}> already exists")
					return
				await interaction.followup.send(f"{key.name}: <@&{value}> has been added to the database")
			case 'remove' :
				if config_key == "VERIFICATION_ADD_ROLE" :
					if not AgeRoleTransactions().permanentdelete(interaction.guild_id, value) :
						await interaction.followup.send(f"{key.name}: <@&{value}> could not be found in database")
						return
					Queue().add(ConfigUtils.log_change(interaction.guild, {key.value : f"role id: {value} removed"},
					                                   user_name=interaction.user.mention))
					await interaction.followup.send(f"{key.name}: <@&{value}> has been removed from the database")
					return

				result = ConfigTransactions().config_key_remove(guildid=interaction.guild.id, key=key.value.upper(),
				                                                value=value)
				if result is False :
					await interaction.followup.send(f"{key.name}: <@&{value}> could not be found in database")
					return
				Queue().add(ConfigUtils.log_change(interaction.guild, {key.value : f"role id: {value} removed"},
				                                   user_name=interaction.user.mention))
				await interaction.followup.send(f"{key.name}: <@&{value}> has been removed from the database")
			case _ :
				raise NotImplementedError

	@app_commands.command(name="cooldown", description="Set a cooldown for how often a user can attempt verification.")
	@app_commands.checks.has_permissions(manage_guild=True)

	async def cooldown(self, interaction: discord.Interaction, cooldown: int) :
		"""
        Set a cooldown period for how often a user can attempt verification in the lobby.
        This can help prevent spam. The cooldown is set in minutes. You can set it to 0 to disable the cooldown entirely.

        **Permissions:**
        - You'll need the `Manage Server` permission to use this command.
        """
		ConfigTransactions().config_unique_add(interaction.guild.id, "cooldown", cooldown, overwrite=True)
		Queue().add(
			ConfigUtils.log_change(interaction.guild, {"cooldown" : cooldown}, user_name=interaction.user.mention,
			                       ))
		await send_response(interaction, f"The cooldown has been set to {cooldown} minutes", ephemeral=True)

	@app_commands.command(name="verification_reminder",
	                      description="💎 Remind members who opened the online verification page but did not finish.")
	@app_commands.checks.has_permissions(manage_guild=True)
	@AccessControl().check_premium()
	async def verification_reminder(self, interaction: discord.Interaction,
	                                minutes: app_commands.Range[int, 0, MAX_VERIFICATION_REMINDER_MINUTES]) :
		"""
        💎 Premium: Sends a DM to members who opened the online verification page but did not finish it within the set number of minutes.
        The DM contains their verification link, so members who got distracted can pick up where they left off. Each link is only reminded once.
        Set it to 0 to turn the reminder off. Only applies when the verification method is Website verification.

        **Permissions:**
        - You'll need the `Manage Server` permission to use this command.
        """
		ConfigTransactions().config_unique_add(interaction.guild.id, VERIFICATION_REMINDER_KEY, minutes, overwrite=True)
		Queue().add(
			ConfigUtils.log_change(interaction.guild, {VERIFICATION_REMINDER_KEY : minutes}, user_name=interaction.user.mention,
			                       ))
		if minutes == 0 :
			await send_response(interaction, "The abandoned verification reminder has been turned off.", ephemeral=True)
			return
		await send_response(interaction,
		                    f"Members who open the verification page but don't finish will be reminded after {minutes} minutes.",
		                    ephemeral=True)

	@app_commands.command(name="verification_mode", description="Set the verification mode for the bot.")
	@app_commands.choices(verification_type=
	[
		Choice(name=VERIFICATION_KEY.replace("_", " ").title(), value=VERIFICATION_KEY),
		Choice(name=REVERIFICATION_KEY.replace("_", " ").title(), value=REVERIFICATION_KEY),

	],
		mode=[Choice(name=method.name, value=method.value) for method in VerificationMethods
	])
	@app_commands.checks.has_permissions(manage_guild=True)
	async def verification_mode(self, interaction: discord.Interaction, verification_type: Choice['str'], mode: Choice['str']) -> None:
		"""
			Allows you to change the verification mode for the bot. Options:
			- Basic (dob)
			- ID verification
			- Basic + ID verification
			- Website verification

			You can set the verification mode for the following types:
			- Verification
			- Reverification

			**Permissions:**
			- You'll need the `Manage Server` permission to use this command.
			- premium required for Reverification, and for ID verification and Basic + ID verification

			Reverification always happens inside Discord, so it can't be set to Website verification.

		"""
		is_premium = AccessControl().is_premium(interaction.guild.id)
		if verification_type.value == REVERIFICATION_KEY :
			if not is_premium :
				return await send_response(interaction,
				                           f"Reverification is a premium feature. "
				                           f"You can find out more about premium here: {os.getenv('DASHBOARD_URL')}",
				                           ephemeral=True)
			# The dashboard has no reverify flow; TOSButton would silently fall back to basic anyway.
			if mode.value == VerificationMethods.WEBSITE :
				return await send_response(interaction,
				                           "Reverification always happens inside Discord, so it can't use Website verification. "
				                           "Please pick Basic, ID verification or Basic + ID verification.",
				                           ephemeral=True)
		if mode.value in PREMIUM_VERIFICATION_METHODS and not is_premium :
			return await send_response(interaction,
			                           f"ID verification and Basic + ID verification are premium features. Basic and Website verification are free. "
			                           f"You can find out more about premium here: {os.getenv('DASHBOARD_URL')}",
			                           ephemeral=True)
		ConfigTransactions().config_unique_add(interaction.guild.id, verification_type.value, mode.value, overwrite=True)
		Queue().add(
			ConfigUtils.log_change(interaction.guild, { verification_type.value: mode.value}, user_name=interaction.user.mention,
			                       ))
		await send_response(interaction, f"The verification mode has been set to {mode.value}", ephemeral=True)



	@app_commands.command(description="Provides a complete overview of the bot's current configuration for your server.")
	@app_commands.checks.has_permissions(manage_guild=True)
	async def view(self, interaction: discord.Interaction, guild: str = None) :
		"""
        This command provides a complete overview of the bot's current configuration for your server.
        It's a handy way to see all your settings at a glance. The configuration will be sent as a text file.

        **Permissions:**
        - You'll need the `Manage Server` permission to use this command.
        - Only the bot developer can view the configuration of other guilds.
        """
		if guild and interaction.user.id != int(os.getenv('DEVELOPER')) :
			return await send_response(interaction, "You do not have permission to view other guilds' configs.",
			                           ephemeral=True)
		roles: list = [x for x in rolechoices.values()]
		other = ["FORUM", "SEARCH"]
		optionsall = list(messagechoices) + list(channelchoices) + list(available_toggles) + list(
			rolechoices)
		await interaction.response.defer()
		with open('config.txt', 'w') as file :
			file.write(f"Config for {interaction.guild.name}: \n\n")
			for item in optionsall :
				info = ConfigData().get_key_or_none(interaction.guild.id if guild is None else int(guild), item)
				file.write(f"{item}: {info}\n")
		await interaction.followup.send(f"Config for {interaction.guild.name if guild is None else guild}",
		                                file=discord.File(file.name))
		os.remove(file.name)
		return None

	@commands.command()
	@commands.is_owner()
	async def cache(self, ctx: commands.Context) :
		"""
        Developer-only maintenance command. It caches a channel's message history for
        internal, one-time migration purposes (a legacy RMR utility) and is not intended
        for, or usable by, regular server administrators. It is hidden from the public
        command documentation.

        **Permissions:**
        - This command can only be used by the bot's owner.
        """
		if ctx.author.id != 188647277181665280 :
			return await ctx.send("This is a DEV command; you do not have permission to use it.")
		count = 0
		historydict = {}
		channel = self.bot.get_channel(454425835064262657)
		await ctx.send('creating cache...')
		time = datetime.datetime.now()
		async for h in channel.history(limit=None, oldest_first=True, before=time) :
			await asyncio.sleep(0.001)
			historydict[h.id] = {}
			historydict[h.id]["author"] = h.author.id
			historydict[h.id]["created"] = h.created_at.strftime('%m/%d/%Y')
			historydict[h.id]["content"] = h.content
			count += 1
		else :
			await ctx.send(f'Cached {count} message(s).')
			print(historydict)
		try :
			os.mkdir('config')
		except :
			pass
		with open('config/history.json', 'w') as f :
			json.dump(historydict, f, indent=4)
			return None


async def setup(bot: commands.Bot) :
	"""Adds the cog to the bot"""
	await bot.add_cog(Config(bot))
