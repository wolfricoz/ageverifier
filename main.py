import os
import re
#imports discord
import discord
from discord.ext import commands
from discord import app_commands
from discord import Interaction
from discord.app_commands import AppCommandError
import logging
import traceback
import pytz
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
#error logging
logger = logging.getLogger('discord')
logger.setLevel(logging.WARN)
handler = logging.FileHandler(filename='bot.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)
logger2 = logging.getLogger('sqlalchemy')
logger2.setLevel(logging.WARN)
handler2 = logging.FileHandler(filename='bot.log', encoding='utf-8', mode='w')
handler2.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger2.addHandler(handler2)
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
                try:
                    tr = db.config(guild.id, None, None, None, None)
                    session.add(tr)
                    session.commit()
                except:
                    session.rollback()
                    session.close()
            p = session.query(db.permissions).filter_by(guild=guild.id).first()
            if p is not None:
                pass
            else:
                try:
                    tr = db.permissions(guild.id, None, None, None, None)
                    session.add(tr)
                    session.commit()
                except:
                    session.rollback()
                    session.close()
        # PRINTS HOW MANY GUILDS / SERVERS THE BOT IS IN.
        formguilds = "\n".join(guilds)
        devroom = bot.get_channel(1022319186950758472)
        await devroom.send(f"{formguilds} \nAgeverifier 1.0 is in {guild_count} guilds. ")
        # SYNCS UP SLASH COMMANDS
        await bot.tree.sync()
        return guilds
    @bot.event
    async def on_guild_join(guild):
        # adds guild to database and creates a config
        exists = session.query(db.config).filter_by(guild=guild.id).first()
        if exists is not None:
            pass
        else:
            try:
                tr = db.config(guild.id, None, None, None, None)
                session.add(tr)
                session.commit()
            except:
                session.rollback()
                session.close()
        p = session.query(db.permissions).filter_by(guild=guild.id).first()
        if p is not None:
            pass
        else:
            try:
                tr = db.permissions(guild.id, None, None, None, None)
                session.add(tr)
                session.commit()
            except:
                session.rollback()
                session.close()
        #CREATES JSON
        await configer.create(guild.id, guild.name)
        #SYNCS COMMANDS
        await bot.tree.sync()
        # sends owner instructions
        await guild.owner.send("Thank you for inviting Age Verifier, please read https://docs.google.com/document/d/1jlDPYCjYO0vpIcDpKAuWBX-iNDyxOTSdLhn_SsVGeks/edit?usp=sharing to set up the bot")
    @bot.event
    async def setup_hook():
        '''Connects the cogs to the bot'''
        for filename in os.listdir("modules"):
            if filename.endswith('.py'):
                await bot.load_extension(f"modules.{filename[:-3]}")
                print({filename[:-3]})
            else:
                print(f'Unable to load {filename[:-3]}')
    tree = bot.tree
    @tree.error
    async def on_app_command_error(
            interaction: Interaction,
            error: AppCommandError
    ):
        await interaction.followup.send(f"Command failed: {error}")
        logging.error(traceback.format_exc())
        #raise error
bot.run(TOKEN)