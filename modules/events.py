import discord

import logging
import re
from discord.ext import commands
from sqlalchemy.orm import sessionmaker
import db
Session = sessionmaker(bind=db.engine)
session = Session()


class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        # Enforces lobby format
        bot = self.bot
        dobreg = re.compile(r"([0-9][0-9]) (1[0-2]|[0]?[0-9]|1)/([0-3]?[0-9])/([0-2][0-9][0-9][0-9])")
        match = dobreg.search(message.content)
        if message.guild is None:
            return
        if message.author.bot:
            return
        # Searches the config for the lobby for a specific guild
        p = session.query(db.permissions).filter_by(guild=message.guild.id).first()
        c = session.query(db.config).filter_by(guild=message.guild.id).first()
        # reminder: change back to c.lobby
        if message.author.get_role(p.mod) is None and message.author.get_role(
                p.admin) is None and message.author.get_role(p.trial) is None:
            if message.channel.id == c.lobby:
                if match:
                    channel = bot.get_channel(c.modlobby)
                    try:
                        await message.add_reaction("🤖")
                    except discord.Forbidden:
                        print(f"No access to add emoji in {message.guild}")
                    if int(match.group(1)) < 18:
                        await channel.send(
                            f"<@&{p.lobbystaff}> {message.author.mention} has given an age under the age of 18: "
                            f"{message.content} (Note: user added to manual ID list)")
                        idchecker = session.query(db.idcheck).filter_by(uid=message.author.id).first()
                        if idchecker is not None:
                            idchecker.check = True
                            session.commit()
                            session.close()
                            
                        else:
                            try:
                                idcheck = db.idcheck(message.author.id, True)
                                session.add(idcheck)
                                session.commit()
                                session.close()
                            except Exception as e:
                                logging.exception(e)
                                session.rollback()
                                session.close()
                                logging.exception("failed to  log to database")
                    elif int(match.group(1)) >= 18:
                        await channel.send(
                            f"<@&{p.lobbystaff}> {message.author.mention} has given {message.content}. "
                            f"You can let them through with `/approve user:{message.author.mention} "
                            f"age:{match.group(1)} dob:{match.group(2)}/{match.group(3)}/{match.group(4)}`")
                    return
                else:
                    channel = bot.get_channel(c.modlobby)
                    await channel.send(f"{message.author.mention} failed to follow the format: {message.content}")
                    await message.channel.send(
                        f"{message.author.mention} Please use format age mm/dd/yyyy "
                        f"\n Example: `122 01/01/1900` "
                        f"\n __**Do not round up your age**__ ")
                    await message.delete()
                    return
        else:
            pass


async def setup(bot):
    await bot.add_cog(Events(bot))
