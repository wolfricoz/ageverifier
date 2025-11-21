"""Config options for the bot."""
import asyncio
import datetime
import json
import logging
import os

from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands
from discord_py_utilities.messages import send_message

from classes.configsetup import ConfigSetup
from databases.controllers.AgeRoleTransactions import AgeRoleTransactions
from databases.controllers.ConfigData import ConfigData
from databases.controllers.ConfigTransactions import ConfigTransactions
from resources.data.config_variables import available_toggles, channelchoices, lobby_approval_toggles, messagechoices, \
	rolechoices
from views.modals.configinput import ConfigInputUnique
from views.select.configselectroles import *


class Config(commands.GroupCog, name="config") :

	def __init__(self, bot: commands.Bot) :
		self.bot = bot

	rolechoices = rolechoices
	channelchoices = channelchoices
	messagechoices = messagechoices
	available_toggles = available_toggles



	@app_commands.command(name='setup')
	@app_commands.checks.has_permissions(manage_guild=True)
	@app_commands.choices(setup_type=[Choice(name=x, value=x) for x in ['dashboard', 'manual', 'auto']])
	async def configsetup(self, interaction: discord.Interaction, setup_type: Choice[str]) :
		"""Sets up the config for the bot."""
		await send_message(interaction.channel,
		                   "For more information about setting up the bot, visit our [Documentation](<https://wolfricoz.github.io/ageverifier/config.html>)")
		logging.info(f"{interaction.guild.name} started {setup_type.value}")
		status: bool = True
		match setup_type.value.lower() :
			case 'dashboard' :
				return await send_response(interaction, f"You can access the dashboard here: https://bots.roleplaymeets.com/")
			case 'manual' :
				await send_message(interaction.channel,
				                   f"You can access the dashboard here for easier setup! https://bots.roleplaymeets.com/")
				status = await ConfigSetup().manual(self.bot, interaction, self.channelchoices, self.rolechoices,
				                                    self.messagechoices)
			case 'auto' :
				status = await ConfigSetup().auto(interaction, self.channelchoices, self.rolechoices, self.messagechoices)

		await send_response(interaction,
		                    "The config has been successfully setup, if you wish to check our toggles you please do /config toggles. Permission checking will commence shortly.",
		                    ephemeral=True)
		if not status :
			return None
		await ConfigSetup().check_channel_permissions(interaction.channel, interaction)
		return None

	@app_commands.command()
	@app_commands.checks.has_permissions(manage_guild=True)
	async def permissioncheck(self, interaction: discord.Interaction) :
		"""Checks the permissions of the bot."""
		await send_response(interaction, f"Starting to check permissions for all the channels!", ephemeral=True)
		await ConfigSetup().check_channel_permissions(interaction.channel, interaction)


	@app_commands.command()
	@app_commands.choices(key=[Choice(name=x, value=x) for x, _ in messagechoices.items()])
	@app_commands.choices(action=[Choice(name=x, value=x) for x in ['set', 'Remove']])
	@app_commands.checks.has_permissions(manage_guild=True)
	async def messages(self, interaction: discord.Interaction, key: Choice[str], action: Choice[str]) :
		"""Sets the messages such as welcome, lobby welcome and reminder messages."""
		match action.value.lower() :
			case 'set' :
				# noinspection PyUnresolvedReferences
				await interaction.response.send_modal(ConfigInputUnique(key=key.value))

			case 'remove' :
				await interaction.response.defer(ephemeral=True)
				result = ConfigTransactions().config_unique_remove(guild_id=interaction.guild.id, key=key.value)
				if result is False :
					await interaction.followup.send(f"{key.value} was not in database")
					return
				await interaction.followup.send(f"{key.value} has been removed from the database")
			case _ :
				raise NotImplementedError

	@app_commands.command()
	@app_commands.choices(action=[Choice(name=x, value=x) for x in ["enabled", "disabled"]],
	                      key=[Choice(name=x, value=x) for x in available_toggles])
	@app_commands.checks.has_permissions(manage_guild=True)
	async def toggles(self, interaction: discord.Interaction, key: Choice[str], action: Choice[str]) :
		"""Enables/Disables the welcome message for the general channel."""
		match action.value.upper() :
			case "ENABLED" :
				ConfigTransactions().toggle(interaction.guild.id, key.value, action.value.upper())


			case "DISABLED" :
				ConfigTransactions().toggle(interaction.guild.id, key.value, action.value.upper())
				if key.value == "LobbyWelcome" :
					return send_response(interaction, f"The lobby welcome message has been disabled. Users will no longer receive a welcome message or the verification button in the lobby channel. To allow users to verify, please use the /lobby command in the channel.", ephemeral=True)
		return await send_response(interaction,f"{key.value} has been set to {action.value}", ephemeral=True)


	@app_commands.command()
	@app_commands.choices(action=[Choice(name=x, value=x) for x in ["enabled", "disabled"]],
	                      key=[Choice(name=x, value=x) for x in lobby_approval_toggles])
	@app_commands.checks.has_permissions(manage_guild=True)
	async def approval_toggles(self, interaction: discord.Interaction, key: Choice[str], action: Choice[str]) :
		"""Customize the approval buttons."""
		match action.value.upper() :
			case "ENABLED" :
				ConfigTransactions().toggle(interaction.guild.id, key.value, action.value.upper())
			case "DISABLED" :
				ConfigTransactions().toggle(interaction.guild.id, key.value, action.value.upper())
		return await send_response(interaction,f"{key.value} has been set to {action.value}", ephemeral=True)

	@app_commands.command()
	@app_commands.choices(key=[Choice(name=f"{x} channel", value=x) for x, _ in channelchoices.items()])
	@app_commands.choices(action=[Choice(name=x, value=x) for x in ["set", "remove"]])
	@app_commands.checks.has_permissions(manage_guild=True)
	async def channels(self, interaction: discord.Interaction, key: Choice[str], action: Choice[str],
	                   value: discord.TextChannel = None) :
		"""adds the channels to the config, you can only add 1 value per option."""
		await interaction.response.defer(ephemeral=True)
		if value is not None :
			value = value.id
		match action.value.lower() :
			case 'set' :
				ConfigTransactions().config_unique_add(guildid=interaction.guild.id, key=key.value, value=value,
				                                     overwrite=True)
				await interaction.followup.send(f"{key.value} has been added to the database with value:\n{value}")
			case 'remove' :
				result = ConfigTransactions().config_unique_remove(guild_id=interaction.guild.id, key=key.value)
				if result is False :
					await interaction.followup.send(f"{key.value} was not in database")
					return
				await interaction.followup.send(f"{key.value} has been removed from the database")
			case _ :
				raise NotImplementedError

	@app_commands.command()
	@app_commands.choices(key=[Choice(name=f"{ke} role", value=ke) for ke, val in rolechoices.items()])
	@app_commands.choices(action=[Choice(name=x, value=x) for x in ['add', 'Remove']])
	@app_commands.checks.has_permissions(manage_guild=True)
	async def roles(self, interaction: discord.Interaction, key: Choice[str], action: Choice[str], value: discord.Role,
	                minimum_age: int = 18, maximum_age: int = 200) :
		"""Add roles to the database, for the bot to use."""
		await interaction.response.defer(ephemeral=True)
		value = value.id
		match action.value.lower() :
			case 'add' :
				if key.value == "add" and maximum_age and minimum_age :
					AgeRoleTransactions().add(guild_id=interaction.guild.id, role_id=value, role_type=key.value,
					                          minimum_age=minimum_age, maximum_age=maximum_age)
					await interaction.followup.send(f"{key.name}: <@&{value}> has been added to the database")
					return

				result = ConfigTransactions().config_key_add(guildid=interaction.guild.id, key=key.value.upper(),
				                                           value=value, overwrite=False)
				if result is False :
					await interaction.followup.send(f"{key.name}: <@&{value}> already exists")
					return
				await interaction.followup.send(f"{key.name}: <@&{value}> has been added to the database")
			case 'remove' :
				if key.value == "add" :
					AgeRoleTransactions().permanentdelete(interaction.guild_id, value)
					await interaction.followup.send(f"{key.name}: <@&{value}> has been removed from the database")
					return

				result = ConfigTransactions().config_key_remove(guildid=interaction.guild.id, key=key.value.upper(),
				                                              value=value)
				if result is False :
					await interaction.followup.send(f"{key.name}: <@&{value}> could not be found in database")
				await interaction.followup.send(f"{key.name}: <@&{value}> has been removed from the database")
			case _ :
				raise NotImplementedError


	@app_commands.command(name="cooldown")
	async def cooldown(self, interaction: discord.Interaction, cooldown: int):
		"""set the cooldown (in minutes) for the lobby verification process. 0 to disable"""
		ConfigTransactions().config_unique_add(interaction.guild.id, "cooldown", cooldown, overwrite=True)
		await send_response(interaction, f"The cooldown has been set to {cooldown} minutes", ephemeral=True)


	@app_commands.command()
	@app_commands.checks.has_permissions(manage_guild=True)
	async def view(self, interaction: discord.Interaction) :
		"""Prints all the config options"""
		roles: list = [x for x in rolechoices.values()]
		other = ["FORUM", "SEARCH"]
		optionsall = list(messagechoices) + list(channelchoices) + list(available_toggles) + list(
			rolechoices)
		await interaction.response.defer()
		with open('config.txt', 'w') as file :
			file.write(f"Config for {interaction.guild.name}: \n\n")
			for item in optionsall :
				info = ConfigData().get_key_or_none(interaction.guild.id, item)
				file.write(f"{item}: {info}\n")
		await interaction.followup.send(f"Config for {interaction.guild.name}", file=discord.File(file.name))
		os.remove(file.name)



	@commands.command()
	@commands.is_owner()
	async def cache(self, ctx: commands.Context) :
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
