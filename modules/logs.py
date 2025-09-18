"""Logs all the happenings of the bot."""
import logging
import os
import time
import traceback
from datetime import datetime, timedelta
from sys import platform

import discord.utils
from discord import Interaction, app_commands
from discord.app_commands import AppCommandError, CheckFailure, command
from discord.ext import commands
from discord_py_utilities.permissions import find_first_accessible_text_channel
from dotenv import load_dotenv

from classes.retired.discord_tools import NoMessagePermissionException
from databases.exceptions.KeyNotFound import KeyNotFound
from discord_py_utilities.messages import NoChannelException, send_message, send_response

load_dotenv('main.env')
channels72 = os.getenv('channels72')
spec = os.getenv('spec')
channels24 = os.getenv('channels24')
single = os.getenv('single')
test = os.getenv('test')
count = 0
os.environ['TZ'] = 'America/New_York'
if platform == "linux" or platform == "linux2" :
	time.tzset()
logfile = f"logs/log-{time.strftime('%m-%d-%Y')}.txt"
removeafter = datetime.now() + timedelta(days=-7)


def extract_datetime_from_logfile(filename) :
	# Split the filename by '-'
	parts = filename.split('-')
	if len(parts) >= 3 :
		# Extract the date part
		date_part = parts[1] + '-' + parts[2] + '-' + parts[3].split('.')[0]
		return datetime.strptime(date_part, '%m-%d-%Y')
	return None


class SafeFormatter(logging.Formatter) :
	"""Formatter that prevents % formatting crashes (mixed mapping vs tuple)."""

	def format(self, record: logging.LogRecord) -> str :
		try :
			return super().format(record)
		except TypeError :
			# Fallback: flatten message and drop args to avoid recursive failure.
			record.msg = str(record.msg)
			record.args = ()
			return super().format(record)


class GatewayPreFormatFilter(logging.Filter) :
	"""Pre-format discord gateway heartbeat warnings to avoid mapping mismatch."""

	def filter(self, record: logging.LogRecord) -> bool :
		if record.name == "discord.gateway" :
			# If mapping style tokens present but args is a tuple, render safely.
			if "%(" in str(record.msg) and isinstance(record.args, tuple) :
				try :
					# Known pattern: "Shard ID %s heartbeat blocked for more than %s seconds."
					# If it accidentally became mapping style somewhere, force manual format.
					if "%s" in record.msg :
						record.msg = record.msg % record.args  # pre-render
						record.args = ()
					else :
						# Mapping placeholders but tuple args: best-effort substitution.
						tuple_args = record.args
						record.msg = record.msg.replace("%(sid)s", str(tuple_args[0] if len(tuple_args) > 0 else "?"))
						record.msg = record.msg.replace("%(total)s", str(tuple_args[1] if len(tuple_args) > 1 else "?"))
						record.args = ()
				except Exception :
					record.args = ()
		return True


if os.path.exists('logs') is False :
	os.mkdir('logs')

if os.path.exists(logfile) is False :
	with open(logfile, 'w') as f :
		f.write("logging started")

for file in os.listdir('logs') :
	date = extract_datetime_from_logfile(file)
	if date is not None and date < removeafter :
		logging.info(f"Removing old log file: {file}")
		os.remove(f'logs/{file}')

with open(logfile, 'a') as f :
	f.write(f"\n\n----------------------------------------------------"
	        f"\nbot started at: {time.strftime('%c %Z')}\n"
	        f"----------------------------------------------------\n\n")

handlers = [
	logging.FileHandler(filename=logfile, encoding='utf-8', mode='a'),
	logging.StreamHandler()
]

safe_fmt = SafeFormatter('(%(asctime)s) %(levelname)s: %(message)s',
                         datefmt='%d/%m/%Y, %H:%M:%S')

for h in handlers :
	h.setFormatter(safe_fmt)

logging.basicConfig(handlers=handlers, level=logging.INFO, force=True)

# Root level
logging.getLogger().setLevel(logging.INFO)

# Existing logger setups
logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
logger2 = logging.getLogger('sqlalchemy')
logger2.setLevel(logging.WARN)


# Attach the filter to the gateway logger (after handlers exist)


class Logging(commands.Cog) :
	def __init__(self, bot) :
		self._old_tree_error = None
		self.bot = bot

	@commands.Cog.listener("on_command_error")
	async def on_command_error(self, ctx: commands.Context, error: commands.CommandError) :
		"""handles chat-based command errors."""
		if isinstance(error, commands.MissingRequiredArgument) :
			await ctx.send("Please fill in the required arguments")
		elif isinstance(error, commands.CommandNotFound) :
			pass
		elif isinstance(error, commands.CheckFailure) :
			await ctx.send("You do not have permission")
		elif isinstance(error, commands.MemberNotFound) :
			await ctx.send("User not found")
		else :
			logger.warning(f"\n{ctx.guild.name} {ctx.guild.id} {ctx.command.name}: {error}")
			channel = self.bot.get_channel(self.bot.DEV)
			with open('error.txt', 'w', encoding='utf-16') as file :
				file.write(str(error))
			await channel.send(
				f"{ctx.guild.name} {ctx.guild.id}: {ctx.author}: {ctx.command.name}",
				file=discord.File(file.name, "error.txt"))
			print('error logged')
			print(traceback.format_exc())

	def cog_load(self) :
		tree = self.bot.tree
		self._old_tree_error = tree.on_error
		tree.on_error = self.on_app_command_error

	def cog_unload(self) :
		tree = self.bot.tree
		tree.on_error = self._old_tree_error

	async def on_fail_message(self, interaction: Interaction, message: str, owner=False, first_channel=True) :
		"""sends a message to the user if the command fails."""
		try :
			if first_channel :
				channel = find_first_accessible_text_channel(interaction.guild)
				await send_message(channel, message, error_mode='ignore')
				return
			if owner :
				await send_message(interaction.guild.owner, message, error_mode='ignore')
				return
			await send_response(interaction, message, ephemeral=True, error_mode='ignore')
		except Exception as e :
			logging.error(e)

	async def on_app_command_error(
			self,
			interaction: Interaction,
			error: AppCommandError
	) :
		"""app command error handler."""
		try :
			data = [f"{a['name']}: {a['value']}" for a in interaction.data['options']]
			formatted_data = ", ".join(data)
		except KeyError :
			formatted_data = "KeyError/No data"
		channel = self.bot.get_channel(self.bot.DEV)
		if isinstance(error, CheckFailure) :
			return await self.on_fail_message(interaction, "You do not have permission.")
		if isinstance(error.original, NoMessagePermissionException) :
			return await self.on_fail_message(interaction,
			                                  f"Missing permission to send message to {interaction.channel.mention} in {interaction.guild.name}. Check permissions: {error.original.message}")
		if isinstance(error.original, discord.Forbidden) :
			return await self.on_fail_message(interaction,
			                                  f"The bot does not have sufficient permission to run this command. Please check: \n* if the bot has permission to post in the channel \n* if the bot is above the role its trying to assign\n* If trying to ban, ensure the bot has the ban permission",
			                                  owner=True)
		if isinstance(error.original, KeyNotFound) :
			return await self.on_fail_message(interaction,
			                                  f"It seems the configuration has not been setup and is missing: {error.original}")

		if isinstance(error.original, NoChannelException) :
			return await self.on_fail_message(interaction,
			                                  "No channel set or does not exist, check the config or fill in the required arguments.",
			                                  first_channel=False)

		if isinstance(error, app_commands.TransformerError) :
			return await self.on_fail_message(interaction,
			                                  "Failed to transform given input to member, please select the user from the list, or use the user's ID.", )
		if isinstance(error, commands.MemberNotFound) :
			return await self.on_fail_message(interaction, "User not found.")
		if isinstance(error, discord.app_commands.errors.TransformerError) :
			return await self.on_fail_message(interaction,
			                                  "Failed to transform given input to member, please select the user from the list, or use the user's ID.")
		if isinstance(error, discord.Forbidden) :
			return await self.on_fail_message(interaction,
			                                  f"The bot does not have sufficient permission to run this command. Please check: \n* if the bot has permission to post in the channel \n* if the bot is above the role its trying to assign")

		with open('error.txt', 'w', encoding='utf-8') as file :
			file.write(traceback.format_exc())
		try :
			await channel.send(
				f"{interaction.guild.name} {interaction.guild.id}: {interaction.user}: {interaction.command.name} with arguments {formatted_data}",
				file=discord.File(file.name, "error.txt"))
		except Exception as e :
			logging.error(e)
		logger.warning(
			f"\n{interaction.guild.name} {interaction.guild.id} {interaction.command.name} with arguments {formatted_data}: {traceback.format_exc()}")

		await self.on_fail_message(interaction, f"Command failed: {error} \nreport this to Rico")
		return None

	# raise error

	@commands.Cog.listener(name='on_command')
	async def print(self, ctx: commands.Context) :
		"""logs the chat command when initiated"""
		server = ctx.guild
		user = ctx.author
		commandname = ctx.command
		logging.debug(f'\n{server.name}({server.id}): {user}({user.id}) issued command: {commandname}')

	@commands.Cog.listener(name='on_app_command_completion')
	async def appprint(self, interaction: Interaction, commandname: command) :
		"""logs the app command when finished."""
		server = interaction.guild
		user = interaction.user
		try :
			logging.debug(
				f'\n{server.name}({server.id}): {user}({user.id}) issued appcommand: `{commandname.name}` with arguments: {interaction.data["options"]}')
		except KeyError :
			logging.debug(
				f'\n{server.name}({server.id}): {user}({user.id}) issued appcommand: `{commandname.name}` with no arguments.')
		except AttributeError :
			logging.debug(f'\n{server.name}({server.id}): {user}({user.id}) issued a command with no data or name.')


# @app_commands.command(name="getlog")
# async def getlog(self, interaction: Interaction) :
# 	"""gets the log file"""
# 	with open(logfile, 'rb') as file :
# 		await send_response(interaction, "Here's the log file.", file=discord.File(file.name, "log.txt"))


async def setup(bot) :
	"""Adds the cog to the bot."""
	await bot.add_cog(Logging(bot))
