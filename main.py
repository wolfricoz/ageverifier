#!/usr/bin/env python
import os

# imports discord
import discord
from discord.ext import commands
# imports dotenv, and loads items
from dotenv import load_dotenv
from sqlalchemy.orm import sessionmaker

load_dotenv("config.env")
prefix = os.getenv('PREFIX')
TOKEN = os.getenv('TOKEN')
# declares bots intents, and allows commands to be ran
intent = discord.Intents.default()
intent.message_content = True
intent.members = True
activity = discord.Activity(type=discord.ActivityType.watching, name="age verificationn")
bot = commands.Bot(command_prefix=prefix, case_insensitive=False, intents=intent, activity=activity,
                   status=discord.Status.online)
from jtest import configer
# imports database and starts it
import db

# error logging
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
        # CREATES A COUNTER TO KEEP TRACK OF HOW MANY GUILDS / SERVERS THE BOT IS CONNECTED TO.
        guild_count = 0
        guilds = []
        # LOOPS THROUGH ALL THE GUILD / SERVERS THAT THE BOT IS ASSOCIATED WITH.

        for guild in bot.guilds:
            # PRINT THE SERVER'S ID AND NAME AND CHECKS IF GUILD CONFIG EXISTS, IF NOT IT CREATES.
            guilds.append(f"- {guild.id} (name: {guild.name})")
            await configer.create(guild.id, guild.name)
            await configer.updateconfig(guild.id)

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
                    session.close()
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
                    session.close()
                except:
                    session.rollback()
                    session.close()
        # PRINTS HOW MANY GUILDS / SERVERS THE BOT IS IN.
        formguilds = "\n".join(guilds)
        devroom = bot.get_channel(1022319186950758472)
        await devroom.send(f"{formguilds} \nAgeverifier 1.2 is in {guild_count} guilds.")
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
                session.close()
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
                session.close()
            except:
                session.rollback()
                session.close()
        # CREATES JSON
        await configer.create(guild.id, guild.name)
        # SYNCS COMMANDS
        await bot.tree.sync()
        # sends owner instructions
        await guild.owner.send(
            "Thank you for inviting Age Verifier, please read https://docs.google.com/document/d/1jlDPYCjYO0vpIcDpKAuWBX-iNDyxOTSdLhn_SsVGeks/edit?usp=sharing to set up the bot")
        log = bot.get_channel(1022319186950758472)
        await log.send(f"Joined {guild}({guild.id})")

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


bot.run(TOKEN)
