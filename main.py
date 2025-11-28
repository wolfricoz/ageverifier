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
from discord_py_utilities.messages import send_message
# IMPORT LOAD_DOTENV FUNCTION FROM DOTENV MODULE.
from dotenv import load_dotenv
from fastapi import FastAPI

import api
from classes import whitelist
from classes.access import AccessControl
from classes.blacklist import blacklist_check
from classes.jsonmaker import Configer
from classes.support.queue import Queue
from databases import current as db
from databases.controllers.ConfigData import ConfigData
from databases.controllers.ServerTransactions import ServerTransactions
from databases.current import Servers
from views.buttons.approvalbuttons import ApprovalButtons
from views.buttons.dobentrybutton import dobentry
from views.buttons.idreviewbuttons import IdReviewButton
from views.buttons.idsubmitbutton import IdSubmitButton
from views.buttons.idverifybutton import IdVerifyButton
from views.buttons.reverifybutton import ReVerifyButton
from views.buttons.verifybutton import VerifyButton
from classes.dashboard.Servers import Servers as DashServers

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
			await bot.start(DISCORD_TOKEN)
		except asyncio.CancelledError :
			# Graceful cancellation
			await bot.close()
			raise

	logging.info("Starting bot...")
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
	Queue().add(ConfigData().load_all_guilds(), 2)
	AccessControl().reload()
	logging.info("Bot starting up")
	devroom = bot.get_channel(bot.DEV)
	# CREATES A COUNTER TO KEEP TRACK OF HOW MANY GUILDS / SERVERS THE BOT IS CONNECTED TO.
	whitelist.create_whitelist(bot.guilds)
	await Configer.create_bot_config()
	Queue().add(bot.tree.sync(), 2)
	Queue().add(devroom.send(f"AgeVerifier is in {len(bot.guilds)} guilds. Ageverifier {version}"), 2)
	logging.info(f"Commands synced, start up done! Connected to {len(bot.guilds)} guilds and {bot.shard_count} shards.")
	bot.add_view(IdVerifyButton())
	bot.add_view(VerifyButton())
	bot.add_view(ReVerifyButton())
	bot.add_view(ApprovalButtons())
	bot.add_view(dobentry())
	bot.add_view(IdSubmitButton())
	bot.add_view(IdReviewButton())
	logging.info("Loaded routers: " + ", ".join(routers))
	Queue().add(check_guilds(devroom))
	await dump_app_commands(bot)


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
	Queue().add(send_message(guild.owner,
	                         f"Thank you for inviting Ageverifier. To help you get started, please read the documentation: https://wolfricoz.github.io/ageverifier/ and visit our [dashboard]({os.getenv("dashboard_url")}) to setup the bot with ease!\n\n"
	                         "Please make sure the bot has permission to post in the channels where you try to run the commands!"))
	ServerTransactions().add(guild.id, active=True)
	dbserver = ServerTransactions().get(guild.id)
	Queue().add(DashServers().update_server(dbserver), 0)


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
	return None


# EXECUTES THE BOT WITH THE SPECIFIED TOKEN.
# EXECUTES THE BOT WITH THE SPECIFIED TOKEN.
async def run() :
	try :
		await bot.start(DISCORD_TOKEN)
	except KeyboardInterrupt :
		exit(0)


# python
async def dump_app_commands(bot, path: str = 'commands.txt') :
	option_type_map = {
		1  : "SUB_COMMAND",
		2  : "SUB_COMMAND_GROUP",
		3  : "STRING",
		4  : "INTEGER",
		5  : "BOOLEAN",
		6  : "USER",
		7  : "CHANNEL",
		8  : "ROLE",
		9  : "MENTIONABLE",
		10 : "NUMBER",
		11 : "ATTACHMENT",
	}

	def fmt_args(opts) :
		parts = []
		for a in opts :
			name = a.get('name')
			req = a.get('required', False)
			parts.append(f"<{name}>" if req else f"[{name}]")
		return " ".join(parts)

	def decode_permissions(val) :
		if not val :
			return "None"
		try :
			p = discord.Permissions(int(val))
			enabled = [k for k, v in p.to_dict().items() if v]
			return ", ".join(enabled) if enabled else "None"
		except Exception :
			return str(val)

	# Group commands by cog name and module
	groups = {}
	for cmd in bot.tree.walk_commands() :
		cog = getattr(cmd, "cog", None)
		if cog :
			cog_name = cog.__class__.__name__
			module = getattr(cog, "__module__", "unknown")
		else :
			cb = getattr(cmd, "callback", None)
			cog_name = "NoCog"
			module = getattr(cb, "__module__", "unknown") if cb else "unknown"

		key = (cog_name, module)
		groups.setdefault(key, []).append(cmd)

	lines = []
	first_group = True
	for (cog_name, module), cmds in groups.items() :
		# header for the cog / location
		if not first_group :
			lines.append("")  # blank line between cog sections
		first_group = False
		lines.append(f"Cog: {cog_name}  —  module: {module}")
		lines.append("")  # blank line after header

		for cmd in cmds :
			try :
				data = cmd.to_dict(tree=bot.tree)
			except TypeError :
				data = cmd.to_dict()

			top_name = data.get('name')
			top_desc = data.get('description', '')
			top_options = data.get('options', [])
			perms_text = decode_permissions(data.get('default_member_permissions'))

			# If there are SUB_COMMAND / SUB_COMMAND_GROUP options, iterate them as commands under the group
			if any(opt.get('type') in (1, 2) for opt in top_options) :
				for sub in top_options :
					if sub.get('type') not in (1, 2) :
						continue
					sub_name = sub.get('name')
					sub_desc = sub.get('description', '')
					sub_args = sub.get('options', [])
					sig = f"/{top_name} {sub_name} {fmt_args(sub_args)}".strip()
					lines.append(sig)
					lines.append(f"  Description: {sub_desc or top_desc}")
					lines.append(f"  Required permissions: {perms_text}")
					if sub_args :
						for a in sub_args :
							a_type = option_type_map.get(a.get('type'), a.get('type'))
							a_req = "required" if a.get('required', False) else "optional"
							a_desc = a.get('description', '')
							lines.append(f"    - {a.get('name')} ({a_req}, type={a_type}) - {a_desc}")
					else :
						lines.append("    - no arguments")
					lines.append("")  # blank line between commands
			else :
				# Top-level command (no subcommands)
				sig = f"/{top_name} {fmt_args(top_options)}".strip()
				lines.append(sig)
				lines.append(f"  Description: {top_desc}")
				lines.append(f"  Required permissions: {perms_text}")
				if top_options :
					for a in top_options :
						a_type = option_type_map.get(a.get('type'), a.get('type'))
						a_req = "required" if a.get('required', False) else "optional"
						a_desc = a.get('description', '')
						lines.append(f"    - {a.get('name')} ({a_req}, type={a_type}) - {a_desc}")
				else :
					lines.append("    - no arguments")
				lines.append("")

	with open(path, 'w', encoding='utf-8') as f :
		f.write('\n'.join(lines))

# @app.on_event("startup")
# async def app_startup() :
# 	# Start Discord bot in a separate thread
# 	threading.Thread(target=lambda : asyncio.run(run())).start()
