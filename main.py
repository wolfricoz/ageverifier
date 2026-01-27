# IMPORT DISCORD.PY. ALLOWS ACCESS TO DISCORD'S API.
# IMPORT THE OS MODULE.
import asyncio
import logging
import os
from contextlib import asynccontextmanager

import discord
import sentry_sdk
from discord.ext import commands
from discord_py_utilities.invites import check_guild_invites
from discord_py_utilities.permissions import find_first_accessible_text_channel
# IMPORT LOAD_DOTENV FUNCTION FROM DOTENV MODULE.
from dotenv import load_dotenv
from fastapi import FastAPI

import api
from classes import whitelist
from classes.access import AccessControl
from classes.blacklist import blacklist_check
from classes.dashboard.Servers import Servers as DashServers
from classes.jsonmaker import Configer
from classes.onboarding import Onboarding
from classes.support.queue import Queue
from databases import current as db
from databases.current import Servers
from databases.transactions.ConfigData import ConfigData
from databases.transactions.ServerTransactions import ServerTransactions
from project.data import VERSION
from views.buttons.approvalbuttons import ApprovalButtons
from views.buttons.dobentrybutton import dobentry
from views.buttons.idreviewbuttons import IdReviewButton
from views.buttons.idsubmitbutton import IdSubmitButton
from views.buttons.idverifybutton import IdVerifyButton
from views.buttons.reverifybutton import ReVerifyButton
from views.buttons.verifybutton import VerifyButton
from views.v2.OnboardingLayout import OnboardingLayout

# Creating database
db.database.create()
# Declares the bots intent

# Load the data from env
load_dotenv('.env')
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
PREFIX = os.getenv("PREFIX")
DBTOKEN = os.getenv("DB")
version = os.getenv('VERSION')
debug = os.getenv('DEBUG')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
activity = discord.Activity(type=discord.ActivityType.watching, name="over the community")
shard_count = 5
if debug :
	shard_count = 1
bot = commands.AutoShardedBot(command_prefix=PREFIX, case_insensitive=False, intents=intents, activity=activity,
                              shard_count=shard_count)

bot.DEV = int(os.getenv("DEV"))

# Sentry Integration
sentry_sdk.init(
	dsn=os.getenv("SENTRY_DSN"),
	# Add data like request headers and IP for users,
	# see https://docs.sentry.io/platforms/python/data-management/data-collected/ for more info
	send_default_pii=True,
)


# Potential fix for not shutting down.
@asynccontextmanager
async def lifespan(app: FastAPI) :
	async def run_bot() :
		try :

			print(DISCORD_TOKEN)
			await bot.start(DISCORD_TOKEN)
		except asyncio.CancelledError :
			# Graceful cancellation
			await bot.close()
			raise
		except Exception as e:
			logging.error(f"Bot encountered an error: {e}", exc_info=True)
			print(f"Bot encountered an error: {e}")
			raise
	bot_task = asyncio.create_task(run_bot())
	logging.info("Bot started.")
	app.state.bot = bot
	try :
		yield
	finally :
		# Trigger shutdown if still running
		if not bot.is_closed() :
			await bot.close()
		# Ensure the task finishes
		if not bot_task.done() :
			bot_task.cancel()
			try :
				await bot_task
			except asyncio.CancelledError :
				pass


app = FastAPI(lifespan=lifespan)
routers = []
for router in api.__all__ :
	try :
		app.include_router(getattr(api, router))
		routers.append(router)
	except Exception as e :
		logging.error(f"Failed to load {router}: {e}")

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
	logging.info(f"{bot.user} has connected to Discord!")
	# Queue().add(ConfigData().load_all_guilds(), 2)
	AccessControl().reload()
	logging.info("Bot starting up")
	devroom = bot.get_channel(bot.DEV)
	# CREATES A COUNTER TO KEEP TRACK OF HOW MANY GUILDS / SERVERS THE BOT IS CONNECTED TO.
	whitelist.create_whitelist(bot.guilds)
	await Configer.create_bot_config()
	Queue().add(bot.tree.sync(), 2)
	Queue().add(devroom.send(f"AgeVerifier is in {len(bot.guilds)} guilds. Ageverifier {VERSION}"), 2)
	logging.info(f"Commands synced, start up done! Connected to {len(bot.guilds)} guilds and {bot.shard_count} shards.")

	logging.info("Loaded routers: " + ", ".join(routers))
	Queue().add(check_guilds(devroom))


async def check_guilds(devroom: discord.TextChannel) :
	for guild in bot.guilds :
		Queue().add(update_guild(guild, devroom), 0)


async def update_guild(guild: discord.Guild, devroom) :
	await blacklist_check(guild, devroom)

	invite = ""
	db_guild: Servers = ServerTransactions().get(guild.id)
	if db_guild :
		invite = db_guild.invite
	ServerTransactions().add(guild.id,
	                         active=True,
	                         name=guild.name,
	                         owner=guild.owner,
	                         member_count=guild.member_count,
	                         invite=await check_guild_invites(bot, guild, invite))
	try :
		bot.invites[guild.id] = await guild.invites()
	except discord.errors.Forbidden :
		print(f"Unable to get invites for {guild.name}")
		try :
			await guild.owner.send("I need the manage server permission to work properly.")
		except discord.errors.Forbidden :
			print(f"Unable to send message to {guild.owner.name} in {guild.name}")
		pass


# This can become its own cog.
@bot.event
async def on_guild_join(guild) :
	# adds user to database
	devroom = bot.get_channel(bot.DEV)
	await devroom.send(f"Ageverifier is now in {len(bot.guilds)}! It just joined:"
	                   f"\nGuild: {guild}({guild.id})"
	                   f"\nOwner: {guild.owner}({guild.owner.id})"
	                   f"\nMember count: {guild.member_count}"
	                   f"\n\nThank you for choosing Ageverifier to keep your server safe.")
	if await blacklist_check(guild, devroom) :
		await guild.owner.send("This server is blacklisted. If this is a mistake then please contact the developer.")
		return
	if whitelist.check_whitelist(guild.id) is False :
		try :
			await guild.owner.send(
				"This server is not whitelisted and the bot will run in a limited mode. Date of births will not be shown.")
		except discord.errors.Forbidden :
			print(f"Unable to send message to {guild.owner.name} in {guild.name}")
	ServerTransactions().add(guild.id,
	                         active=True,
	                         name=guild.name,
	                         owner=guild.owner,
	                         member_count=guild.member_count,
	                         invite=await check_guild_invites(bot, guild)
	                         )
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
	channel = find_first_accessible_text_channel(guild)
	if not channel:
		channel = guild.owner
	await Onboarding().join_message(channel)
	ServerTransactions().add(guild.id, active=True)
	dbserver = ServerTransactions().get(guild.id)
	Queue().add(DashServers().update_servers([dbserver]), 0)


@bot.event
async def on_guild_remove(guild) :
	devroom = bot.get_channel(bot.DEV)
	await devroom.send(f"Left {guild.name}({guild.id})")


# cogloader
@bot.event
async def setup_hook() :
	directories = ["modules", "listeners", "tasks"]
	loaded = []
	for directory in directories :
		try :
			# Loop through all the files in the directory, and load them.
			for filename in os.listdir(directory) :

				if filename.endswith('.py') :



					await bot.load_extension(f"{directory}.{filename[:-3]}")
					loaded.append(f"{directory}.{filename[:-3]}")
				else :
					logging.info(f'Unable to load {filename[:-3]} in {directory}')
		except FileNotFoundError :
			os.mkdir(directory)
			pass
	logging.info(f'Loaded {len(loaded)} modules: {", ".join(loaded)}')
	bot.add_view(IdVerifyButton())
	bot.add_view(VerifyButton())
	bot.add_view(ReVerifyButton())
	bot.add_view(ApprovalButtons())
	bot.add_view(dobentry())
	bot.add_view(IdSubmitButton())
	bot.add_view(IdReviewButton())
	bot.add_view(OnboardingLayout())

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
	return None


# EXECUTES THE BOT WITH THE SPECIFIED TOKEN.
# EXECUTES THE BOT WITH THE SPECIFIED TOKEN.



# @app.on_event("startup")
# async def app_startup() :
# 	# Start Discord bot in a separate thread
# 	threading.Thread(target=lambda : asyncio.run(run())).start()
# bot.run(DISCORD_TOKEN)