import json
import re
import traceback
from abc import ABC, abstractmethod
from datetime import datetime

import discord
from dateutil.relativedelta import relativedelta
from discord import app_commands
from discord.ext import commands
from sqlalchemy.orm import sessionmaker

import adefs
import db
import logging

import jtest

Session = sessionmaker(bind=db.engine)
session = Session()


class AgeCalc(ABC):
    @abstractmethod
    def agechecker(self, arg1, arg2):
        age = arg1
        dob = str(arg2)
        dob_object = datetime.strptime(dob, "%m/%d/%Y")
        today = datetime.now()
        a = relativedelta(today, dob_object)
        age_calculate = a.years - int(age)
        return age_calculate

    def regex(arg2):
        datetime.strptime(arg2, '%m/%d/%Y')
        dob = str(arg2)
        dob_object = re.search(r"([0-1]?[0-9])/([0-3]?[0-9])/([0-2][0-9][0-9][0-9])", dob)
        month = dob_object.group(1).zfill(2)
        day = dob_object.group(2).zfill(2)
        year = dob_object.group(3)
        fulldob = f"{month}/{day}/{year}"
        print(fulldob)
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

    # async def removemessage(ctx, bot, user):
    #     c = session.query(db.config).filter_by(guild=ctx.guild.id).first()
    #     print(c.lobby)
    #     channel = bot.get_channel(c.lobby)
    #     messages = channel.history(limit=100)
    #     count = 0
    #     async for message in messages:
    #         if message.author == user or user in message.mentions and count < 10:
    #             count += 1
    #             print(message.id)
    #             await message.delete()

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

    async def waitingadd(interaction, guildid, user):
        with open(f"jsons/{guildid}.json") as f:
            addroles = json.load(f)
        for role in addroles["waitingrole"]:
            r = interaction.guild.get_role(role)
            await user.add_roles(r)
        else:
            print("Finished adding")

    async def waitingrem(interaction, guildid, user):
        with open(f"jsons/{guildid}.json") as f:
            addroles = json.load(f)
        for role in addroles["waitingrole"]:
            try:
                r = interaction.guild.get_role(role)
                await user.remove_roles(r)
            except Exception as e:
                logging.error(f"failed to add roles. \n {e}")
        else:
            print("Finished removing")

    async def welcome(interaction, user, general):
        with open(f"jsons/{interaction.guild.id}.json") as f:
            data = json.load(f)
            if data['welcomeusers'] is True:
                try:
                    exists = session.query(db.config).filter_by(guild=interaction.guild.id).first()

                    welcomemessage = data["welcome"]
                    await general.send(
                        f"Welcome to {interaction.guild.name}, {user.mention}! {welcomemessage}")

                except:
                    await interaction.channel.send(
                        "Channel **general** not set. Use ?config general #channel to fix this.")
            else:
                pass
    @abstractmethod
    async def removemessage(interaction, bot, user):
        c = session.query(db.config).filter_by(guild=interaction.guild.id).first()
        channel = bot.get_channel(c.lobby)
        messages = channel.history(limit=100)
        format = re.compile(r"failed to follow the format", flags=re.MULTILINE)
        count = 0
        async for message in messages:
            if message.author == user or user in message.mentions and count < 10:
                count += 1
                await message.delete()
        channel = bot.get_channel(c.modlobby)
        messages = channel.history(limit=100)
        count = 0
        async for message in messages:
            if user in message.mentions and count < 5:
                if message.author.bot:
                    vmatch = format.search(message.content)
                    if vmatch is not None:
                        pass
                    else:
                        count += 1
                        await message.delete()

class dblookup(ABC):

    @abstractmethod
    def dobsave(self, userid: discord.Member, dob):
        exists = session.query(db.user).filter_by(uid=userid.id).first()
        if exists is not None:
            pass
        else:
            try:
                tr = db.user(userid.id, dob)
                session.add(tr)
                session.commit()
            except:
                print("Database error, rolled back")
                session.rollback()
                session.close()

    async def dobsaveid(self, userid: int, dob):
        exists = session.query(db.user).filter_by(uid=userid).first()
        if exists is not None:
            pass
        else:
            try:
                tr = db.user(userid, dob)
                session.add(tr)
                session.commit()
            except:
                print("Database error, rolled back")
                session.rollback()
                session.close()

    def dobcheck(self, userid: discord.Member, dob):
        exists = session.query(db.user).filter_by(uid=userid.id).first()
        if exists.dob == dob:
            return True
        else:
            return False

    @abstractmethod
    def idcheckchecker(self, userid: discord.Member):
        exists = session.query(db.idcheck).filter_by(uid=userid.id).first()
        if exists is not None:
            if exists.check:
                return True
            else:
                return False
        else:
            return False

    @abstractmethod
    def idcheckeradd(self, userid: int):
        idchecker = session.query(db.idcheck).filter_by(uid=userid).first()
        if idchecker is not None:
            idchecker.check = True
            session.commit()
        else:
            try:
                idcheck = db.idcheck(userid, True)
                session.add(idcheck)
                session.commit()
            except:
                session.rollback()
                session.close()
                logging.exception("failed to  log to database")

    @abstractmethod
    def idcheckerremove(self, userid: int):
        idchecker = session.query(db.idcheck).filter_by(uid=userid).first()
        if idchecker is not None:
            idchecker.check = False
            session.commit()
        else:
            try:
                idcheck = db.idcheck(userid, False)
                session.add(idcheck)
                session.commit()
            except:
                session.rollback()
                session.close()
                logging.exception("failed to  log to database")


class lobby(commands.Cog, name="Lobby"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="dblookup", description="Check user's age in DB. only works on users in server")
    @adefs.check_slash_admin_roles()
    async def dblookup(self, interaction: discord.Interaction, user: discord.Member):
        await interaction.response.defer(ephemeral=True)
        try:
            exists = session.query(db.user).filter_by(uid=user.id).first()
        except:
            await interaction.followup.send(f"{user.mention} has not been found")
        if exists is None:
            await interaction.followup.send(f"{user.mention} has not been found")
        else:
            await interaction.followup.send(f"""__**DB LOOKUP**__
user: <@{exists.uid}>
UID: {exists.uid}
DOB: {exists.dob}""")

    @app_commands.command(name="dbremove",
                          description="DEV: Removes user from database. This can be requested by users.")
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
            await interaction.followup.send(
                "Please contact Rico Stryker#6666 or send an email to roleplaymeetsappeals@gmail.com to have the entry removed")

    @app_commands.command(name="approve",
                          description="Approve a user to enter your server. this command checks ages and logs them")
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
        regdob = AgeCalc.regex(dob)
        print(regdob)
        bot = self.bot
        if dblookup.idcheckchecker(self, user) is True:
            channel = bot.get_channel(c.modlobby)
            await channel.send(f"<@&{a.admin}> user {user.mention} was flagged for manual ID check.")
        else:
            if AgeCalc.agechecker(self, age, regdob) == 0:
                try:
                    dblookup.dobsave(self, user, regdob)
                except:
                    logging.critical(f"Failed to add user to DB: {user.id} {dob}")
                    interaction.followup.send(f"Failed to add user to DB: {user.id} {dob}, report to Rico.")
                print(dblookup.dobcheck(self, user, regdob))
                if dblookup.dobcheck(self, user, regdob) is True:
                    # Role adding
                    # await ctx.send('This user\'s age is correct')
                    await AgeCalc.addroles(interaction, interaction.guild.id, user)
                    await AgeCalc.remroles(interaction, interaction.guild.id, user)
                    await AgeCalc.waitingrem(interaction, interaction.guild.id, user)
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
                        await interaction.channel.send(
                            "Channel **agelobby** not set. Use /config channel agelobby #channel to fix this.")
                    # welcomes them in general chat.
                    general = bot.get_channel(c.general)
                    await AgeCalc.welcome(interaction, user, general)
                    # this deletes user info
                    await interaction.followup.send(f"{user} has been let through the lobby")
                    if jtest.configer.read(interaction.guild.id, "delete") is False:
                        return
                    await AgeCalc.removemessage(interaction, self.bot, user)

                else:
                    try:
                        await AgeCalc.waitingadd(interaction, interaction.guild.id, user)
                    except:
                        logging.exception("Couldn't add waiting role(s)")
                    channel = bot.get_channel(925193288997298226)
                    try:
                        channel = bot.get_channel(c.modlobby)
                        u = session.query(db.user).filter_by(uid=user.id).first()

                        await channel.send(
                            f'<@&{a.admin}> User {user.mention}\'s dob ({regdob}) does not match a previously given dob ({u.dob}) and has been given Waiting in Lobby. \n \n To check previously given ages or edit them use: /dblookup or /agefix')
                    except:
                        await interaction.channel.send(
                            "Channel **modlobby** not set. Use /config channel modlobby #channel to fix this.")
                    await interaction.followup.send(f"DOB ERROR: {user}")

            else:
                try:
                    await AgeCalc.waitingadd(interaction, interaction.guild.id, user)
                except:
                    logging.exception("Couldn't add waiting role(s)")
                try:
                    channel = bot.get_channel(c.modlobby)
                    await channel.send(
                        f'<@&{a.admin}> User {user.mention}\'s age does not match and has been timed out. User gave {age} but dob indicates {AgeCalc.agecheckfail(regdob)}')
                except:
                    await interaction.channel.send(
                        "Channel **modlobby** not set. Use /config channel modlobby #channel to fix this.")
                await interaction.followup.send(f"AGE ERROR: {user}")

    @app_commands.command(name="returnlobby", description="Returns user to the lobby by removing roles")
    @adefs.check_slash_db_roles()
    async def returnlobby(self, interaction: discord.Interaction, user: discord.Member):
        """Command sends users back to the lobby and removes roles"""
        bot = self.bot
        await interaction.response.defer()
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
        await interaction.followup.send(
            f"{user.mention} has been moved back to the lobby by {interaction.user.mention}")

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
        regdob = AgeCalc.regex(dob)
        userdata = session.query(db.user).filter_by(uid=user.id).first()
        userdata.dob = regdob
        session.commit()
        await channel.send(f"""**updated user info:** 
user: {user.mention}
UID: {user.id} 
Age: {age}
DOB: {regdob}


Entry updated by: {interaction.user}""")
        await interaction.followup.send(f"{user.name}'s data has been updated to: {age} {regdob}")

    @app_commands.command(name="agefixid", description="Edits database entry with the correct date of birth")
    @adefs.check_slash_admin_roles()
    async def agefixid(self, interaction: discord.Interaction, userid: str, age: int, dob: str):
        await interaction.response.defer(ephemeral=True)
        c = session.query(db.config).filter_by(guild=interaction.guild.id).first()
        agelog = c.agelog
        channel = self.bot.get_channel(agelog)
        regdob = AgeCalc.regex(dob)
        userdata = session.query(db.user).filter_by(uid=userid).first()
        userdata.dob = regdob
        session.commit()
        await channel.send(f"""**updated user info:**  
UID: {userid} 
Age: {age}
DOB: {regdob}

Entry updated by: {interaction.user}""")
        await interaction.followup.send(f"{userid}'s data has been updated to: {age} {regdob}")

    @app_commands.command(name="ageadd", description="Add ages to the database")
    @adefs.check_slash_db_roles()
    async def ageadd(self, interaction: discord.Interaction, user: str, age: str, dob: str):
        await interaction.response.defer()
        c = session.query(db.config).filter_by(guild=interaction.guild.id).first()
        agelog = c.agelog
        channel = self.bot.get_channel(agelog)
        regdob = AgeCalc.regex(dob)
        await dblookup.dobsaveid(self, int(user), regdob)
        await channel.send(f"""**USER ADDED**
Age: {age}
DOB: {dob}
UID: {user} 

Entry updated by: {interaction.user}""")
        await interaction.followup.send(f"User was added to the database")

    @app_commands.command(name="idverify", description="approves user for ID verification.")
    @adefs.check_slash_admin_roles()
    async def idverify(self, interaction: discord.Interaction, user: discord.Member, age: str, dob: str):
        await interaction.response.defer(ephemeral=True)
        c = session.query(db.config).filter_by(guild=interaction.guild.id).first()
        agelog = c.agelog
        channel = self.bot.get_channel(agelog)
        regdob = AgeCalc.regex(dob)
        try:
            userdata = session.query(db.user).filter_by(uid=user.id).first()
            if userdata is not None:
                userdata.dob = regdob
            else:
                dblookup.dobsave(self, user, regdob)
            idchecker = session.query(db.idcheck).filter_by(uid=user.id).first()
            if idchecker is not None:
                idchecker.check = False
                session.commit()
            else:
                try:
                    idcheck = db.idcheck(user.id, False)
                    session.add(idcheck)
                    session.commit()
                except:
                    session.rollback()
                    session.close()
                    logging.exception("failed to  log to database")
            await channel.send(f"""**USER ID VERIFICATION**
user: {user.mention}
Age: {age}
DOB: {dob}
UID: {user.id} 
**ID VERIFIED BY:** {interaction.user}""")
            await interaction.followup.send(f"Entry for {user} updated to: {age} {regdob}")
        except:
            session.rollback()
            session.close()
            await interaction.followup.send(f"Command failed: {traceback.format_exc()}")
    @app_commands.command(name="idadd", description="add a user to manual ID list")
    @adefs.check_slash_db_roles()
    async def addverify(self, interaction: discord.Interaction, userid: str):
        await interaction.response.defer(ephemeral=True)
        dblookup.idcheckeradd(self, userid)
        await interaction.followup.send(f"Added user {userid} to the ID list")

    @app_commands.command(name="idremove", description="remove a user to manual ID list")
    @adefs.check_slash_admin_roles()
    async def remverify(self, interaction: discord.Interaction, userid: str):
        await interaction.response.defer(ephemeral=True)
        dblookup.idcheckerremove(self, userid)
        await interaction.followup.send(f"Removed user {userid} to the ID list")


async def setup(bot: commands.Bot):
    await bot.add_cog(lobby(bot))


session.commit()
