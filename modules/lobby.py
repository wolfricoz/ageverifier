import json

import discord
from discord.ext import commands
from abc import ABC, abstractmethod
import db
import adefs
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, column
from datetime import datetime, timedelta
import re
import typing
from discord import app_commands
Session = sessionmaker(bind=db.engine)
session = Session()

class agecalc(ABC):
    @abstractmethod
    def agechecker(self, arg1, arg2):
        age = arg1
        dob = str(arg2)
        dob_object = datetime.strptime(dob, "%m/%d/%Y")
        today = datetime.now()
        leapyear = ((today - dob_object) / 365.25) / 4
        deltad = leapyear - timedelta(days=1)
        agechecker = ((today - dob_object) - deltad) / 365
        age_output = str(agechecker).split()[0]
        age_calculate = int(age_output) - int(age)
        print(age_calculate)
        return age_calculate
    def regex(arg2):
        dob = str(arg2)
        dob_object = re.search(r"([0-1]?[0-9])\/([0-3]?[0-9])\/([0-2][0-9][0-9][0-9])", dob)
        month = dob_object.group(1).zfill(2)
        day = dob_object.group(2).zfill(2)
        year = dob_object.group(3)
        fulldob = f"{month}/{day}/{year}"
        return fulldob
    def agecheckfail(arg1):
        bot = commands.Bot
        from datetime import datetime, timedelta
        dob = str(arg1)
        dob_object = datetime.strptime(dob, "%m/%d/%Y")
        today = datetime.now()
        leapyear = ((today - dob_object) / 365.25) / 4
        deltad = leapyear - timedelta(days=1)
        agechecker = ((today - dob_object) - deltad) / 365
        print(agechecker)
        age_output = str(agechecker).split()[0]
        return age_output
    async def removemessage(ctx, bot, user):
        c = session.query(db.config).filter_by(guild=ctx.guild.id).first()
        print(c.lobby)
        channel = bot.get_channel(c.lobby)
        messages = channel.history(limit=100)
        count = 0
        async for message in messages:
            if message.author == user or user in message.mentions and count < 10:
                count += 1
                print(message.id)
                await message.delete()
    async def addroles(interaction, guildid, user):
        with open(f"jsons/{guildid}.json") as f:
            addroles = json.load(f)
        for role in addroles["addrole"]:
            r = interaction.guild.get_role(role)
            await user.add_roles(r)
        else:
            print("Finished adding")
    async def remroles(interaction, guildid, user):
        with open(f"jsons/{guildid}.json") as f:
            addroles = json.load(f)
        for role in addroles["remrole"]:
            r = interaction.guild.get_role(role)
            await user.remove_roles(r)
        else:
            print("Finished removing")
    async def welcome(interaction, user, general):
        try:

            exists = session.query(db.config).filter_by(guild=interaction.guild.id).first()

            with open(f"jsons/{interaction.guild.id}.json") as f:
                data = json.load(f)
            welcomemessage = data["welcome"]
            await general.send(
                f"Welcome to {interaction.guild.name}, {user.mention}! {welcomemessage}")

        except:
            await interaction.channel.send("Channel **general** not set. Use ?config general #channel to fix this.")

class dblookup(ABC):

    @abstractmethod
    def dobsave(self, userid: discord.Member, dob):
        exists = session.query(db.user).filter_by(uid=userid.id).first()
        if exists is not None:
            pass
        else:
            tr = db.user(userid.id, dob)
            session.add(tr)
            session.commit()

    def dobcheck(self, userid: discord.Member, dob):
        exists = session.query(db.user).filter_by(uid=userid.id).first()
        if exists.dob == dob:
            return True
        else:
            return False

class lobby(commands.Cog, name="Lobby"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="dblookup", description="Check user's age in DB. only works on users in server")
    @adefs.check_slash_admin_roles()
    async def dblookup(self, interaction: discord.Interaction, userid: discord.Member):
        await interaction.response.defer(ephemeral=True)
        try:
            exists = session.query(db.user).filter_by(uid=userid.id).first()
        except:
            await interaction.followup.send(f"{userid.mention} has not been found")
        if exists is None:
            await interaction.followup.send(f"{userid.mention} has not been found")
        else:
            await interaction.followup.send(f"""__**DB LOOKUP**__
user: <@{exists.uid}>
UID: {exists.uid}
DOB: {exists.dob}""")

    @app_commands.command(name="dbremove", description="DEV: Removes user from database. This can be requested by users.")
    @adefs.check_slash_admin_roles()
    async def dbremoveid(self, interaction: discord.Interaction, userid: str):
        await interaction.response.defer(ephemeral=True)
        user = int(userid)
        if interaction.user.id == 188647277181665280:
            try:
                exists = session.query(db.user).filter_by(uid=user).first()
                session.delete(exists)
                session.commit()
                await interaction.followup.send("Removal complete")
            except:
                await interaction.followup.send("Removal failed")
        else:
            await interaction.followup.send("Please contact Rico Stryker#6666 or send an email to roleplaymeetsappeals@gmail.com to have the entry removed")

    @app_commands.command(name="approve", description="Approve a user to enter your server. this command checks ages and logs them")
    @adefs.check_slash_db_roles()
    async def sapprove(self, interaction: discord.Interaction, user: discord.Member, age: int, dob: str) -> None:
        """Command to let users through the lobby, checks ages and logs them."""
        await interaction.response.defer(ephemeral=True)
        c = session.query(db.config).filter_by(guild=interaction.guild.id).first()
        a = session.query(db.permissions).filter_by(guild=interaction.guild.id).first()
        lobbyid = c.lobby
        agelog = c.agelog
        modlobby = c.modlobby
        general = c.general
        regdob = agecalc.regex(dob)
        print(regdob)
        bot = self.bot
        if agecalc.agechecker(self, age, regdob) == 0:
            dblookup.dobsave(self, user, regdob)
            print(dblookup.dobcheck(self, user, regdob))
            if dblookup.dobcheck(self, user, regdob) is True:
                # Role adding
                # await ctx.send('This user\'s age is correct')
                # TODO: Make a better system for this.
                await agecalc.addroles(interaction, interaction.guild.id, user)
                await agecalc.remroles(interaction, interaction.guild.id, user)
                # output for lobby ages
                from datetime import datetime
                username = user.mention
                userid = user.id
                userjoin = user.joined_at
                userjoinformatted = userjoin.strftime('%m/%d/%Y %I:%M:%S %p')
                executed = datetime.now().strftime('%m/%d/%Y %I:%M:%S %p')
                print(userjoinformatted)
                staff = interaction.user
                try:
                    log = bot.get_channel(c.agelog)
                    await log.send(
                        f"user: {username}\n Age: {age} \n DOB: {regdob} \n User info:  UID: {userid} \n joined at: {userjoinformatted} \n \n executed: {executed} \n staff: {staff}")
                except:
                    await interaction.channel.send("Channel **agelobby** not set. Use ?config agelobby #channel to fix this.")

                # welcomes them in general chat.
                general = bot.get_channel(c.general)
                await agecalc.welcome(interaction, user, general)
                # this deletes user info
                await agecalc.removemessage(interaction, bot, user)
            else:
                waiting = discord.utils.get(interaction.guild.roles, name="Waiting in Lobby")
                await user.add_roles(waiting)
                channel = bot.get_channel(925193288997298226)
                try:
                    channel = bot.get_channel(c.modlobby)
                    u = session.query(db.user).filter_by(uid=user.id).first()

                    await channel.send(
                        f'<@&{a.admin}> User {user.mention}\'s dob ({regdob}) does not match a previously given dob ({u.dob}) and has been given Waiting in Lobby. \n \n To check previously given ages or edit them use: ?agelookup or ?agefix')
                except:
                    await interaction.channel.send("Channel **modlobby** not set. Use ?config modlobby #channel to fix this.")

        else:
            waiting = discord.utils.get(interaction.guild.roles, name="Waiting in Lobby")
            await user.add_roles(waiting)
            print(agecalc.agecheckfail(arg2))
            try:
                channel = bot.get_channel(c.modlobby)
                await channel.send(
                     f'<@&{a.admin}> User {user.mention}\'s age does not match and has been timed out. User gave {age} but dob indicates {agecalc.agecheckfail(arg2)}')
            except:
                await interaction.channel.send("Channel **modlobby** not set. Use ?config modlobby #channel to fix this.")
        await interaction.followup.send(f"{user} has been let through the lobby")

    @app_commands.command(name="returnlobby", description="Returns user to the lobby by removing roles")
    @adefs.check_slash_db_roles()
    async def returnlobby(self, interaction: discord.Interaction, user: discord.Member):
        """Command sends users back to the lobby and removes roles"""
        bot = self.bot
        await interaction.response.defer()
        from datetime import datetime, timedelta
        with open(f"jsons/{interaction.guild.id}.json") as f:
            addroles = json.load(f)
        for role in addroles["addrole"]:
            r = interaction.guild.get_role(role)
            await user.remove_roles(r)
        else:
            print("Finished removing")
        with open(f"jsons/{interaction.guild.id}.json") as f:
            addroles = json.load(f)
        for role in addroles["remrole"]:
            r = interaction.guild.get_role(role)
            await user.add_roles(r)
        else:
            print("Finished adding")
        await interaction.followup.send(f"{user.mention} has been moved back to the lobby by {interaction.user.mention}")


    @app_commands.command(name="agecheck", description="Calculates the age of the user based on the dob.")
    @adefs.check_slash_db_roles()
    async def agecheck(self, interaction: discord.Interaction, dob: str, ):
        await interaction.response.defer(ephemeral=True)
        bot = self.bot
        from datetime import datetime, timedelta
        dob = str(dob)
        dob_object = datetime.strptime(dob, "%m/%d/%Y")
        today = datetime.now()
        leapyear = ((today - dob_object) / 365.25) / 4
        deltad = leapyear - timedelta(days=1)
        agechecker = ((today - dob_object) - deltad) / 365
        print(agechecker)
        age_output = str(agechecker).split()[0]
        await interaction.followup.send('this users age is: {}'.format(age_output) + " years.")

    @app_commands.command(name="agefix", description="Edits database entry with the correct date of birth")
    @adefs.check_slash_admin_roles()
    async def agefix(self, interaction: discord.Interaction, user: discord.Member, age: int, dob: str):
        await interaction.response.defer(ephemeral=True)
        c = session.query(db.config).filter_by(guild=interaction.guild.id).first()
        agelog = c.agelog
        channel = self.bot.get_channel(agelog)
        regdob = agecalc.regex(dob)
        userdata = session.query(db.user).filter_by(uid=user.id).first()
        userdata.dob = regdob
        session.commit()
        await channel.send(f"""user: {user.mention}
Age: {age}
DOB: {regdob}
User info:  UID: {user.id} 

Entry updated by: {interaction.user}""")
        await interaction.followup.send(f"{user.name}'s data has been updated to: {age} {regdob}")


async def setup(bot: commands.Bot):
    await bot.add_cog(lobby(bot))

session.commit()