# IMPORT DISCORD.PY. ALLOWS ACCESS TO DISCORD'S API.
# IMPORT THE OS MODULE.
import asyncio
import logging
import os
import threading
from contextlib import asynccontextmanager

import discord
from discord.ext import commands
# IMPORT LOAD_DOTENV FUNCTION FROM DOTENV MODULE.
from dotenv import load_dotenv
from fastapi import FastAPI

from api import config_router, age_router
from classes import whitelist
from classes.blacklist import blacklist_check
from classes.databaseController import ConfigData, ServerTransactions
from classes.jsonmaker import Configer
from classes.support.discord_tools import send_message
from classes.support.queue import queue
from databases import current as db
from views.buttons.idverifybutton import IdVerifyButton

# Creating database
db.database.create()
# Declares the bots intent

# Load the data from env
load_dotenv('rmrbot/.env')
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
PREFIX = os.getenv("PREFIX")
DBTOKEN = os.getenv("DB")
version = os.getenv('VERSION')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
activity = discord.Activity(type=discord.ActivityType.watching, name="over the community")

bot = commands.AutoShardedBot(command_prefix=PREFIX, case_insensitive=False, intents=intents, activity=activity)

bot.DEV = int(os.getenv("DEV"))


@asynccontextmanager
async def lifespan(app: FastAPI) :
	threading.Thread(target=lambda : asyncio.run(run())).start()
	app.state.bot = bot
	yield
	await bot.close()


app = FastAPI(lifespan=lifespan)
app.include_router(config_router)
app.include_router(age_router)


if os.getenv("KEY") is None :
	quit("No encryption key found in .env")


# Move to devtools?
@bot.command()
@commands.is_owner()
async def stop(ctx) :
	await ctx.send("Rmrbot shutting down")
	exit()


bot.invites = {}


# EVENT LISTENER FOR WHEN THE BOT HAS SWITCHED FROM OFFLINE TO ONLINE.
@bot.event
async def on_ready() :
	logging.info("Bot starting up")
	devroom = bot.get_channel(bot.DEV)
	# CREATES A COUNTER TO KEEP TRACK OF HOW MANY GUILDS / SERVERS THE BOT IS CONNECTED TO.
	guilds = []
	whitelist.create_whitelist(bot.guilds)
	await Configer.create_bot_config()
	for guild in bot.guilds :
		queue().add(blacklist_check(guild, devroom), priority=2)
		ServerTransactions().add(guild.id, active=True)
		ConfigData().load_guild(guild.id)
		guilds.append(guild.name)
		try :
			bot.invites[guild.id] = await guild.invites()
		except discord.errors.Forbidden :
			print(f"Unable to get invites for {guild.name}")
			try :
				await guild.owner.send("I need the manage server permission to work properly.")
			except discord.errors.Forbidden :
				print(f"Unable to send message to {guild.owner.name} in {guild.name}")
			pass
	formguilds = "\n".join(guilds)
	await bot.tree.sync()
	await devroom.send(f"AgeVerifier is in {len(guilds)} guilds. Ageverifier {version}")
	logging.info(f"Commands synced, start up done! Connected to {len(guilds)} guilds and {bot.shard_count} shards.")
	logging.info(f"Guilds: {formguilds}")
	bot.add_view(IdVerifyButton())
	return guilds


# This can become its own cog.
@bot.event
async def on_guild_join(guild) :
	# adds user to database
	devroom = bot.get_channel(bot.DEV)
	await devroom.send(f"Joined {guild.name}({guild.id})")
	if await blacklist_check(guild, devroom) :
		await guild.owner.send("This server is blacklisted. If this is a mistake then please contact the developer.")
		return
	if whitelist.check_whitelist(guild.id) is False :
		try :
			await guild.owner.send(
				"This server is not whitelisted and the bot will run in a limited mode. Date of births will not be shown.")
		except discord.errors.Forbidden :
			print(f"Unable to send message to {guild.owner.name} in {guild.name}")
	ServerTransactions().add(guild.id, True)
	ConfigData().load_guild(guild.id)
	try :
		bot.invites[guild.id] = await guild.invites()
	except discord.errors.Forbidden :
		print(f"Unable to get invites for {guild.name}")
		try :
			await guild.owner.send("I need the manage server permission to work properly.")
		except discord.errors.Forbidden :
			print(f"Unable to send message to {guild.owner.name} in {guild.name}")
		pass
	queue().add(send_message(guild.owner,
	                         "Thank you for inviting Ageverifier. To help you get started, please read the documentation: https://wolfricoz.github.io/ageverifier/ and visit our [dashboard](https://bots.roleplaymeets.com/) to setup the bot with ease!\n\n"
	                         "Please make sure the bot has permission to post in the channels where you try to run the commands!"))


@bot.event
async def on_guild_remove(guild) :
	devroom = bot.get_channel(bot.DEV)
	await devroom.send(f"Left {guild.name}({guild.id})")


# cogloader
@bot.event
async def setup_hook() :
	bot.lobbyages = bot.get_channel(454425835064262657)
	for filename in os.listdir("modules") :

		if filename.endswith('.py') :
			await bot.load_extension(f"modules.{filename[:-3]}")
			print({filename[:-3]})
		else :
			print(f'Unable to load {filename[:-3]}')


@bot.command(aliases=["cr", "reload"])
@commands.has_permissions(administrator=True)
async def cogreload(ctx) :
	filesloaded = []
	for filename in os.listdir("modules") :
		if filename.endswith('.py') :
			await bot.reload_extension(f"modules.{filename[:-3]}")
			filesloaded.append(filename[:-3])
	fp = ', '.join(filesloaded)
	await ctx.send(f"Modules loaded: {fp}")
	await bot.tree.sync()


@bot.command()
async def leave_server(ctx, guildid: int) :
	if ctx.author.id != 188647277181665280 :
		return await ctx.send("You are not allowed to use this command.")
	guild = bot.get_guild(guildid)
	await guild.leave()
	await ctx.send(f"Left {guild}")


# EXECUTES THE BOT WITH THE SPECIFIED TOKEN.
# EXECUTES THE BOT WITH THE SPECIFIED TOKEN.
async def run() :
	try :
		await bot.start(DISCORD_TOKEN)
	except KeyboardInterrupt :
		exit(0)


# @app.on_event("startup")
# async def app_startup() :
# 	# Start Discord bot in a separate thread
# 	threading.Thread(target=lambda : asyncio.run(run())).start()

