import discord
from discord import app_commands
from discord.ext import commands
from sqlalchemy.orm import sessionmaker

import db
import jtest
from jtest import configer

Session = sessionmaker(bind=db.engine)
session = Session()
from discord.app_commands import Choice


class config(commands.GroupCog, name="config"):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="role", description="**CONFIG COMMAND**: Sets up the channels for the bot.")
    @app_commands.choices(option=[
        Choice(name="Admin", value="admin"),
        Choice(name="Mod", value="mod"),
        Choice(name="Trial", value="trial"),
        Choice(name="Lobby Staff", value="lobbystaff")
    ])
    @app_commands.checks.has_permissions(manage_guild=True)
    async def crole(self, interaction: discord.Interaction, option: Choice[str], input: discord.Role):
        await interaction.response.defer(ephemeral=True)
        c = session.query(db.config).filter_by(guild=interaction.guild.id).first()
        p = session.query(db.permissions).filter_by(guild=interaction.guild.id).first()
        match option.value:
            case "admin":
                p.admin = input.id
                session.commit()
                session.close()
                await interaction.followup.send(f"Value **admin** role has been updated to {input.id}")
            case "mod":
                p.mod = input.id
                session.commit()
                session.close()
                await interaction.followup.send(f"Value **mod** role has been updated to {input.id}")
            case "trial":
                p.trial = input.id
                session.commit()
                session.close()
                await interaction.followup.send(f"Value **trial** role has been updated to {input.id}")
            case "lobbystaff":
                p.lobbystaff = input.id
                session.commit()
                session.close()
                await interaction.followup.send(f"Value **lobbystaff** role has been updated to {input.id}")
            case default:
                await interaction.followup.send("""**Config options**: 
• admin @role
• mod @role
• trial @role
• lobbystaff @role""")

    @app_commands.command(name="channel", description="**CONFIG COMMAND**: Sets up the channels for the bot")
    @app_commands.choices(option=[
        Choice(name="Lobby", value="lobby"),
        Choice(name="Age logging channel", value="agelog"),
        Choice(name="Moderator Lobby", value="modlobby"),
        Choice(name="General Chat", value="general")
    ])
    @app_commands.checks.has_permissions(manage_guild=True)
    async def cchannel(self, interaction: discord.Interaction, option: Choice[str], input: discord.TextChannel):
        print(interaction.guild.id)
        c = session.query(db.config).filter_by(guild=interaction.guild.id).first()
        p = session.query(db.permissions).filter_by(guild=interaction.guild.id).first()
        await interaction.response.defer(ephemeral=True)
        match option.value:
            case "lobby":
                c.lobby = input.id
                session.commit()
                session.close()
                await interaction.followup.send(f"Value **lobby** channel has been updated to {input.id}")
            case "agelog":
                c.agelog = input.id
                session.commit()
                session.close()
                await interaction.followup.send(f"Value **agelog** channel has been updated to {input.id}")
            case "modlobby":
                c.modlobby = input.id
                session.commit()
                session.close()
                await interaction.followup.send(f"Value **modlobby** channel has been updated to {input.id}")
            case "general":
                c.general = input.id
                session.commit()
                session.close()
                await interaction.followup.send(f"Value **general** channel has been updated to {input.id}")
            case default:
                await interaction.followup.send("""**Config options**: 
• lobby #channel
• agelog #channel
• modlobby #channel
• general #channel
""")

    @app_commands.command(name="welcome",
                          description="**CONFIG COMMAND**: turns on/off welcome message for when /approve is used")
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.choices(option=[
        Choice(name="on", value="True"),
        Choice(name="off", value="False")
    ])
    async def welcome(self, interaction: discord.Interaction, option: Choice[str]):
        await interaction.response.defer(ephemeral=True)
        match option.value:
            case "True":
                await configer.welcome(interaction.guild.id, interaction, "welcomeusers", True)
            case "False":
                await configer.welcome(interaction.guild.id, interaction, "welcomeusers", False)
            case default:
                await interaction.followup.send("ERROR: couldn't edit. Contact Rico")

    @app_commands.command(name="delete", description="**CONFIG COMMAND**: turns on/off deletion of messages.")
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.choices(option=[
        Choice(name="on", value="True"),
        Choice(name="off", value="False")
    ])
    async def lobbydelete(self, interaction: discord.Interaction, option: Choice[str]):
        await interaction.response.defer(ephemeral=True)
        match option.value:
            case "True":
                configer.trueorfalse(interaction.guild.id, "delete", True)
                await interaction.followup.send("Automatic deletion of messages is now **__on__**")
            case "False":
                configer.trueorfalse(interaction.guild.id, "delete", False)
                await interaction.followup.send("Automatic deletion of messages is now **__off__**")
            case default:
                await interaction.followup.send("ERROR: couldn't edit. Contact Rico")

    @app_commands.command(name="welcomemessage",
                          description="**CONFIG COMMAND**: changes welcome message for when /approve is used")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def welcomemessage(self, interaction: discord.Interaction, message: str):
        await interaction.response.defer(ephemeral=True)
        await configer.welcome(interaction.guild.id, interaction, "welcome", message)

    @app_commands.command(name="view")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def viewconfig(self, interaction: discord.Interaction):
        await interaction.response.defer()

        channels = session.query(db.config).filter_by(guild=interaction.guild.id).first()
        roles = session.query(db.permissions).filter_by(guild=interaction.guild.id).first()
        await interaction.followup.send(
            f"{await jtest.configer.viewconfig(interaction, interaction.guild.id)}\nAdmin role: {roles.admin}\nMod role: {roles.mod}\nTrial role: {roles.trial}\nLobbystaff (ping)role: {roles.lobbystaff}\n\n Lobby channel: {channels.lobby}\n Agelog channel: {channels.agelog}\nmodlobby channel: {channels.modlobby}\ngeneral channel: {channels.general}")


async def setup(bot: commands.Bot):
    await bot.add_cog(config(bot))


session.commit()
