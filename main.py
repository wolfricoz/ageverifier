import os
import re
#imports discord
import discord
from discord.ext import commands
from discord import app_commands
from discord import Interaction
from discord.app_commands import AppCommandError
#imports dotenv, and loads items
from dotenv import load_dotenv
load_dotenv("config.env")
prefix = os.getenv('PREFIX')
TOKEN = os.getenv('TOKEN')
#declares bots intents, and allows commands to be ran
intent = discord.Intents.default()
intent.message_content = True
intent.members = True
bot = commands.Bot(command_prefix=prefix, case_insensitive=False, intents=intent)
from jtest import configer
#imports database and starts it
import db
exec(open("db.py").read())
Session = sessionmaker(bind=db.engine)
session = Session()
@bot.command()
async def sync(ctx):
    s = await ctx.bot.tree.sync()
    await ctx.send(f"bot has synced {len(s)} servers")
class main():
    @bot.event
    async def on_ready():
        #devroom = bot.get_channel(987679198560796713)
        # CREATES A COUNTER TO KEEP TRACK OF HOW MANY GUILDS / SERVERS THE BOT IS CONNECTED TO.
        guild_count = 0
        guilds = []
        # LOOPS THROUGH ALL THE GUILD / SERVERS THAT THE BOT IS ASSOCIATED WITH.

        for guild in bot.guilds:
            # PRINT THE SERVER'S ID AND NAME AND CHECKS IF GUILD CONFIG EXISTS, IF NOT IT CREATES.
            guilds.append(f"- {guild.id} (name: {guild.name})")
            await configer.create(guild.id, guild.name)

            # INCREMENTS THE GUILD COUNTER.
            guild_count = guild_count + 1
            # ADDS GUILDS TO MYSQL DATABASE
            exists = session.query(db.config).filter_by(guild=guild.id).first()
            if exists is not None:
                pass
            else:
                tr = db.config(guild.id, None, None, None, None)
                session.add(tr)
                session.commit()
            p = session.query(db.permissions).filter_by(guild=guild.id).first()
            if p is not None:
                pass
            else:
                tr = db.permissions(guild.id, None, None, None, None)
                session.add(tr)
                session.commit()
        # PRINTS HOW MANY GUILDS / SERVERS THE BOT IS IN.
        formguilds = "\n".join(guilds)
        #await devroom.send(f"{formguilds} \nRMRbot is in {guild_count} guilds. ")
        # SYNCS UP SLASH COMMANDS
        await bot.tree.sync()
        return guilds

    async def on_guild_join(guild):
        # adds guild to database and creates a config
        exists = session.query(db.config).filter_by(guild=guild.id).first()
        if exists is not None:
            pass
        else:
            tr = config(guild.id, None, None, None, None)
            session.add(tr)
            session.commit()
        p = session.query(db.permissions).filter_by(guild=guild.id).first()
        if p is not None:
            pass
        else:
            tr = permissions(guild.id, None, None, None, None)
            session.add(tr)
            session.commit()
        await configer.create(guild.id, guild.name)

    @bot.event
    async def setup_hook():
        for filename in os.listdir("modules"):

            if filename.endswith('.py'):
                await bot.load_extension(f"modules.{filename[:-3]}")
                print({filename[:-3]})
            else:
                print(f'Unable to load {filename[:-3]}')

    @bot.event
    async def on_command_error(ctx, interaction: discord.Interaction, error):
        if isinstance(error, commands.MissingRequiredArgument):
            import time
            await ctx.send("Please fill in the required arguments")
        elif isinstance(error, commands.CommandNotFound):
            pass
        elif isinstance(error, commands.CheckFailure):
            await ctx.send("You do not have permission")
        elif isinstance(error, commands.MemberNotFound):
            await ctx.send("User not found")
        elif isinstance(error, commands.CommandInvokeError):
            await ctx.send("Command failed: See log.")
            await ctx.send(error)
            raise error
        else:
            await interaction.response.send_message(error)
            await ctx.send(error)
            raise error

    tree = bot.tree
    @tree.error
    async def on_app_command_error(
            interaction: Interaction,
            error: AppCommandError
    ):
        await interaction.channel.send(f"Command failed: {error}")
    """    @bot.listen()
    async def on_message(message):
        # Enforces lobby format
        dobreg = re.compile("([0-9][0-9]) (1[0-2]|[0]?[0-9]|1)\/([0-3]?[0-9])\/([0-2][0-9][0-9][0-9])")
        match = dobreg.search(message.content)
        if message.guild is None:
            return
        if message.author.bot:
            return
        # Searches the config for the lobby for a specific guild
        p = session.query(db.permissions).filter_by(guild=message.guild.id).first()
        c = session.query(db.config).filter_by(guild=message.guild.id).first()
        staff = [p.mod, p.admin, p.trial]
        # reminder: change back to c.lobby
        if message.author.get_role(p.mod) is None and message.author.get_role(
                p.admin) is None and message.author.get_role(p.trial) is None:
            if message.channel.id == c.lobby:
                if match:
                    channel = bot.get_channel(c.modlobby)
                    await message.add_reaction("🤖")
                    if int(match.group(1)) < 18:
                        await channel.send(
                            f"<@&{p.lobbystaff}> {message.author.mention} has given an age under the age of 18: {message.content}")
                    if int(match.group(1)) > 18 and not int(match.group(1)) > 20:
                        await channel.send(
                            f"<@&{p.lobbystaff}> user has given age. You can let them through with `?18a {message.author.mention} {message.content}`")
                    elif int(match.group(1)) > 21 and not int(match.group(1)) > 24:
                        await channel.send(
                            f"<@&{p.lobbystaff}> user has given age. You can let them through with `?21a {message.author.mention} {message.content}`")
                    elif int(match.group(1)) > 25:
                        await channel.send(
                            f"<@&{p.lobbystaff}> user has given age. You can let them through with `?25a {message.author.mention} {message.content}`")
                    return
                else:
                    try:
                        await message.author.send(
                            f"Please use format age mm/dd/yyyy \n Example: `122 01/01/1900` \n __**Do not round up your age**__ \n You can input your age and dob at: <#{c.lobby}>")
                    except:
                        await message.channel.send(
                            f"Couldn't message {message.author.mention}! Please use format age mm/dd/yyyy \n Example: `122 01/01/1900")
                    await message.delete()
                    return
        else:
            pass
    
    """

bot.run(TOKEN)