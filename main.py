# IMPORT DISCORD.PY. ALLOWS ACCESS TO DISCORD'S API.
# IMPORT THE OS MODULE.
import os

import discord
from discord.ext import commands
# IMPORT LOAD_DOTENV FUNCTION FROM DOTENV MODULE.
from dotenv import load_dotenv

from classes import permissions
from classes.databaseController import ConfigData, ConfigTransactions, UserTransactions
from databases import current as db

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
activity = discord.Activity(type=discord.ActivityType.watching, name="over RMR")
bot = commands.Bot(command_prefix=PREFIX, case_insensitive=False, intents=intents, activity=activity)
bot.DEV = int(os.getenv("DEV"))

if os.getenv("KEY") is None:
    quit("No encryption key found in .env")

# Move to devtools?
@bot.command()
@commands.is_owner()
async def stop(ctx):
    await ctx.send("Rmrbot shutting down")
    exit()


bot.invites = {}


# EVENT LISTENER FOR WHEN THE BOT HAS SWITCHED FROM OFFLINE TO ONLINE.
@bot.event
async def on_ready():
    devroom = bot.get_channel(bot.DEV)
    # CREATES A COUNTER TO KEEP TRACK OF HOW MANY GUILDS / SERVERS THE BOT IS CONNECTED TO.
    guilds = []
    for guild in bot.guilds:

        ConfigTransactions.server_add(guild.id)
        ConfigData().load_guild(guild.id)
        guilds.append(guild.name)
        try:
            bot.invites[guild.id] = await guild.invites()
        except discord.errors.Forbidden:
            print(f"Unable to get invites for {guild.name}")
            try:
                await guild.owner.send("I need the manage server permission to work properly.")
            except discord.errors.Forbidden:
                print(f"Unable to send message to {guild.owner.name} in {guild.name}")
            pass
    formguilds = "\n".join(guilds)
    await bot.tree.sync()
    await devroom.send(f"{formguilds} \nAgeVerifier is in {len(guilds)} guilds. Ageverifier {version}")
    print("Commands synced, start up _done_")
    return guilds


# This can become its own cog.
@bot.event
async def on_guild_join(guild):
    # adds user to database
    ConfigTransactions.server_add(guild.id)
    ConfigData().load_guild(guild.id)
    try:
        bot.invites[guild.id] = await guild.invites()
    except discord.errors.Forbidden:
        print(f"Unable to get invites for {guild.name}")
        try:
            await guild.owner.send("I need the manage server permission to work properly.")
        except discord.errors.Forbidden:
            print(f"Unable to send message to {guild.owner.name} in {guild.name}")
        pass


@bot.event
async def on_member_join(member):
    UserTransactions.add_user_empty(member.id)


# cogloader
@bot.event
async def setup_hook():
    bot.lobbyages = bot.get_channel(454425835064262657)
    for filename in os.listdir("modules"):

        if filename.endswith('.py'):
            await bot.load_extension(f"modules.{filename[:-3]}")
            print({filename[:-3]})
        else:
            print(f'Unable to load {filename[:-3]}')


@bot.command(aliases=["cr", "reload"])
@permissions.check_roles_admin()
async def cogreload(ctx):
    filesloaded = []
    for filename in os.listdir("modules"):
        if filename.endswith('.py'):
            await bot.reload_extension(f"modules.{filename[:-3]}")
            filesloaded.append(filename[:-3])
    fp = ', '.join(filesloaded)
    await ctx.send(f"Modules loaded: {fp}")
    await bot.tree.sync()


@bot.command()
async def leave_server(ctx, guildid: int):
    if ctx.author.id != 188647277181665280:
        return await ctx.send("You are not allowed to use this command.")
    guild = bot.get_guild(guildid)
    await guild.leave()
    await ctx.send(f"Left {guild}")


# EXECUTES THE BOT WITH THE SPECIFIED TOKEN.
bot.run(DISCORD_TOKEN)
