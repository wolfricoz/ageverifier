"""this module handles the lobby."""
import datetime
import os

import discord
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands
from sqlalchemy import True_

import classes.permissions as permissions
from classes.AgeCalculations import AgeCalculations
from classes.databaseController import UserTransactions, ConfigData, VerificationTransactions
from classes.encryption import Encryption
from classes.helpers import has_onboarding, welcome_user, invite_info
from classes.lobbyprocess import LobbyProcess
from classes.support.discord_tools import send_response, send_message
from classes.whitelist import check_whitelist
from databases.current import database, Users
from views.buttons.agebuttons import AgeButtons
from views.buttons.confirmButtons import confirmAction
from views.buttons.dobentrybutton import dobentry
from views.buttons.verifybutton import VerifyButton


class Lobby(commands.GroupCog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.index = 0
        self.bot.add_view(VerifyButton())
        self.bot.add_view(AgeButtons())
        self.bot.add_view(dobentry())

    @app_commands.command(name="button")
    @app_commands.checks.has_permissions(administrator=True)
    async def verify_button(self, interaction: discord.Interaction, text: str):
        """Verification button for the lobby; initiates the whole process"""
        await interaction.channel.send(text, view=VerifyButton())

    @app_commands.command()
    @app_commands.choices(operation=[Choice(name=x, value=x) for x in
                                     ['add', 'update', 'delete', 'get']])
    @app_commands.checks.has_permissions(manage_messages=True)
    async def database(self, interaction: discord.Interaction, operation: Choice['str'], userid: str, dob: str = None):
        """One stop shop to handle all age entry management. Only add 1 date of birth per user."""
        userid = int(userid)
        age_log = ConfigData().get_key_int(interaction.guild.id, "lobbylog")
        age_log_channel = interaction.guild.get_channel(age_log)
        dev_channel = self.bot.get_channel(int(os.getenv('DEV')))
        if not check_whitelist(interaction.guild.id) and not permissions.check_dev(interaction.user.id):
            await send_response(interaction, "[NOT_WHITELISTED] This command is limited to whitelisted servers.")
            return
        try:
            await interaction.response.defer(ephemeral=True)
        except discord.InteractionResponded:
            pass
        match operation.value.upper():
            case "UPDATE":
                if await AgeCalculations.validatedob(dob, interaction) is False:
                    return
                UserTransactions.update_user_dob(userid, dob, interaction.guild.name)
                await send_response(interaction, f"Updated <@{userid}>'s dob to {dob}")
                await LobbyProcess.age_log(age_log_channel, userid, dob, interaction, "updated")
                await send_message(dev_channel, f"<@{userid}>'s dob updated in {interaction.guild.name} by {interaction.user.name}.")

            case "DELETE":
                if not interaction.user.guild_permissions.administrator:
                    await interaction.followup.send("You are not an admin")
                    return
                if UserTransactions.user_delete(userid, interaction.guild.name) is False:
                    await interaction.followup.send(f"Can't find entry: <@{userid}>")
                    return
                await send_response(interaction, f"Deleted entry: <@{userid}>")
                await send_message(dev_channel, f"<@{userid}>'s dob deleted in {interaction.guild.name} by {interaction.user.name}.")
            case "ADD":
                if await AgeCalculations.validatedob(dob, interaction) is False:
                    return
                UserTransactions.add_user_full(str(userid), dob, interaction.guild.name)
                await send_response(interaction, f"<@{userid}> added to the database with dob: {dob}")
                await LobbyProcess.age_log(age_log_channel, userid, dob, interaction)
                await send_message(dev_channel, f"<@{userid}>'s dob added in {interaction.guild.name} by {interaction.user.name}.")
            case "GET":
                user: Users = UserTransactions.get_user(userid)
                discord_user = self.bot.get_user(userid)
                if not permissions.check_dev(interaction.user.id) and (discord_user not in interaction.guild.members or user.server != interaction.guild.name):
                    await interaction.followup.send("The user is not in the server and the date of birth was not added in this server.")
                    return
                await send_response(interaction,
                                    f"**__USER INFO__**\n"
                                    f"user: <@{user.uid}>\n"
                                    f"dob: {Encryption().decrypt(user.date_of_birth)}\n"
                                    f"Last updated in: {user.server}")

    @app_commands.command()
    @app_commands.choices(process=[Choice(name=x, value=x) for x in
                                   ["True", "False"]])
    @app_commands.checks.has_permissions(administrator=True)
    async def idverify(self, interaction: discord.Interaction, process: Choice['str'],
                       user: discord.User, dob: str):
        """ID verifies user. process True will put the user through the lobby."""
        if check_whitelist(interaction.guild.id) is False and not permissions.check_dev(interaction.user.id):
            await send_response(interaction, "[NOT_WHITELISTED] This command is limited to whitelisted servers. Please contact the developer `ricostryker` to verify the user.")
            return
        try:
            await interaction.response.defer(ephemeral=True)
        except discord.InteractionResponded:
            pass
        lobbylog = ConfigData().get_key_int(interaction.guild.id, "lobbylog")

        agelog = interaction.guild.get_channel(lobbylog)
        await AgeCalculations.validatedob(dob, interaction)
        print(f"matching time: {process.value.upper()}")
        match process.value.upper():
            case "TRUE":
                print("true")
                VerificationTransactions.idverify_update(user.id, dob, interaction.guild.name)
                await interaction.followup.send(
                        f"{user.mention} has been ID verified with date of birth: {dob}")
                await agelog.send(f"""**USER ID VERIFICATION**
user: {user.mention}
DOB: {dob}
UID: {user.id} 
**ID VERIFIED BY:** {interaction.user}""")
                age = AgeCalculations.dob_to_age(dob)
                await LobbyProcess.approve_user(interaction.guild, user, dob, age, interaction.user.name)
            case "FALSE":
                VerificationTransactions.idverify_update(user.id, dob, interaction.guild.name)
                await interaction.followup.send(
                        f"{user.mention} has been ID verified with date of birth: {dob}")
                await agelog.send(f"""**USER ID VERIFICATION**
user: {user.mention}
DOB: {dob}
UID: {user.id} 
**ID VERIFIED BY:** {interaction.user}""")

    @app_commands.command()
    @app_commands.checks.has_permissions(manage_messages=True)
    async def returnlobby(self, interaction: discord.Interaction, user: discord.Member):
        """returns user to lobby; removes the roles."""
        await interaction.response.defer()
        add_roles: list = ConfigData().get_key(interaction.guild.id, "add")
        add = list(add_roles)
        rem: list = ConfigData().get_key(interaction.guild.id, "rem")
        returns: list = ConfigData().get_key(interaction.guild.id, "return")
        print('data retrieved')
        rm = []
        ra = []
        for role in rem:
            r = interaction.guild.get_role(role)
            ra.append(r)
        for role in add + returns:
            r = interaction.guild.get_role(role)
            rm.append(r)
        print('roles retrieved')
        await user.remove_roles(*rm, reason="returning to lobby")
        await user.add_roles(*ra, reason="returning to lobby")
        print('roles changed')
        await interaction.followup.send(
                f"{user.mention} has been moved back to the lobby by {interaction.user.mention}")

    @app_commands.command()
    @app_commands.checks.has_permissions(manage_messages=True)
    async def agecheck(self, interaction: discord.Interaction, dob: str):
        """Checks the age of a dob"""
        age = AgeCalculations.dob_to_age(dob)
        await interaction.response.send_message(f"As of today {dob} is {age} years old", ephemeral=True)

    @commands.command(name="approve")
    @commands.has_permissions(manage_messages=True)
    async def approve(self, ctx: commands.Context, user: discord.Member, age: int, dob: str):
        """allows user to enter"""
        dob = AgeCalculations.regex(dob)
        await LobbyProcess.approve_user(ctx.guild, user, dob, age, ctx.author.name)
        await ctx.message.delete()

    @app_commands.command()
    @app_commands.checks.has_permissions(administrator=True)
    async def purge(self, interaction: discord.Interaction, days: int = 14):
        """This command will kick all the users that have not been processed through the lobby with the given days."""
        lobby_config = ConfigData().get_key_int(interaction.guild.id, "lobby")
        lobby_channel = interaction.guild.get_channel(lobby_config)
        if days > 14:
            days = 14
            await interaction.channel.send("Max days is 14, setting to 14")

        view = confirmAction()
        await view.send_message(interaction, f"Are you sure you want to purge the lobby of users that have not been processed in the last {days} days?")
        await view.wait()
        if view.confirmed is False:
            await interaction.followup.send("Purge cancelled")
            return
        days_to_datetime = datetime.datetime.now() - datetime.timedelta(days=days)
        kicked = []
        async for x in lobby_channel.history(limit=None, after=days_to_datetime):
            if x.author.bot is False:
                continue
            for a in x.mentions:
                try:
                    await a.kick()
                    kicked.append(f"{a.name}({a.id})")
                except Exception as e:
                    print(f"unable to kick {a} because {e}")
            await x.delete()
        with open("config/kicked.txt", "w") as file:
            str_kicked = "\n".join(kicked)
            file.write(f"these users were removed during the purge:\n")
            file.write(str_kicked)
        await interaction.channel.send(f"{interaction.user.mention} Kicked {len(kicked)}", file=discord.File(file.name, "kicked.txt"))
        os.remove("config/kicked.txt")

    @app_commands.command()
    @app_commands.choices(operation=[Choice(name=x, value=x) for x in
                                     ['add', 'update', 'get', 'delete']])
    @app_commands.choices(idcheck=[Choice(name=x, value=y) for x, y in
                                   {"Yes": "True", "No": "False"}.items()])
    @app_commands.checks.has_permissions(manage_messages=True)
    async def idcheck(self, interaction: discord.Interaction, operation: Choice['str'], idcheck: Choice['str'],
                      userid: str, reason: str = None):
        """adds user to id check or removes them"""
        userid = int(userid)
        if idcheck.value == "True":
            idcheck = True
        elif idcheck.value == "False":
            idcheck = False
        await interaction.response.defer(ephemeral=False)
        match operation.value.upper():
            case "UPDATE":
                if reason is None:
                    await interaction.followup.send(f"Please include a reason")
                    return
                VerificationTransactions.update_check(userid, reason, idcheck)
                await interaction.followup.send(
                        f"<@{userid}>'s userid entry has been updated with reason: {reason} and idcheck: {idcheck}")
            case "ADD":
                if reason is None:
                    await interaction.followup.send(f"Please include a reason")
                    return
                VerificationTransactions.add_idcheck(userid, reason, idcheck)
                await interaction.followup.send(
                        f"<@{userid}>'s userid entry has been added with reason: {reason} and idcheck: {idcheck}")
            case "GET":
                user = VerificationTransactions.get_id_info(userid)
                if user is None:
                    await interaction.followup.send("Not found")
                    return
                await interaction.followup.send(f"**__USER INFO__**\n"
                                                f"user: <@{user.uid}>\n"
                                                f"Reason: {user.reason}\n"
                                                f"idcheck: {user.idcheck}\n"
                                                f"idverifier: {user.idverified}\n"
                                                f"verifieddob: {user.verifieddob}\n")
            case "DELETE":
                if not interaction.user.guild_permissions.administrator:
                    await interaction.followup.send("You are not an admin")
                    return
                if VerificationTransactions.set_idcheck_to_false(userid) is False:
                    await interaction.followup.send(f"Can't find entry: <@{userid}>")
                    return
                await interaction.followup.send(f"Deleted entry: <@{userid}>")

    # Event

    @commands.Cog.listener('on_member_join')
    async def add_to_db(self, member):
        UserTransactions.add_user_empty(member.id)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """posts the button for the user to verify with."""
        if await has_onboarding(member.guild):
            return
        await welcome_user(member)

    # @commands.Cog.listener()
    # async def on_member_update(self, before: discord.Member, after: discord.Member):
    #     if before.flags != after.flags:
    #         # Perform the desired action when the member's flags change
    #         if before.flags.completed_onboarding is False and after.flags.completed_onboarding is True:
    #             await welcome_user(after)
    #             await invite_info(self.bot, after)


async def setup(bot):
    """Adds the cog to the bot."""
    await bot.add_cog(Lobby(bot))
