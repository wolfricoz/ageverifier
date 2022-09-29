import discord
from discord import app_commands
from discord.ext import commands
from abc import ABC, abstractmethod
import db
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, column
import typing
from discord import app_commands
from jtest import configer
import logging
Session = sessionmaker(bind=db.engine)
session = Session()
from discord.app_commands import Choice
class config(commands.GroupCog, name="config"):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
    #TODO: Change this into 2 commands, config channel and config role
    @app_commands.command(name="role", description="**CONFIG COMMAND**: Sets up the channels for the bot.")
    @app_commands.choices(option=[
        Choice(name="Admin", value="admin"),
        Choice(name="Mod", value="mod"),
        Choice(name="Trial", value="trial"),
        Choice(name="Lobby Staff", value="lobbystaff")
    ])
    @app_commands.checks.has_permissions(manage_guild=True)
    async def crole(self, interaction: discord.Interaction, option: Choice[str], input:  discord.Role):
        await interaction.response.defer(ephemeral=True)
        c = session.query(db.config).filter_by(guild=interaction.guild.id).first()
        p = session.query(db.permissions).filter_by(guild=interaction.guild.id).first()
        match option.value:
            case "admin":
                p.admin = input.id
                session.commit()
                await interaction.followup.send(f"Value **admin** role has been updated to {input.id}")
            case "mod":
                p.mod = input.id
                session.commit()
                await interaction.followup.send(f"Value **mod** role has been updated to {input.id}")
            case "trial":
                p.trial = input.id
                session.commit()
                await interaction.followup.send(f"Value **trial** role has been updated to {input.id}")
            case "lobbystaff":
                p.lobbystaff = input.id
                session.commit()
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
    async def cchannel(self, interaction: discord.Interaction, option: Choice[str], input:  discord.TextChannel):
        print(interaction.guild.id)
        c = session.query(db.config).filter_by(guild=interaction.guild.id).first()
        p = session.query(db.permissions).filter_by(guild=interaction.guild.id).first()
        await interaction.response.defer(ephemeral=True)
        match option.value:
            case "lobby":
                c.lobby = input.id
                session.commit()
                await interaction.followup.send(f"Value **lobby** channel has been updated to {input.id}")
            case "agelog":
                c.agelog = input.id
                session.commit()
                await interaction.followup.send(f"Value **agelog** channel has been updated to {input.id}")
            case "modlobby":
                c.modlobby = input.id
                session.commit()
                await interaction.followup.send(f"Value **modlobby** channel has been updated to {input.id}")
            case "general":
                c.general = input.id
                session.commit()
                await interaction.followup.send(f"Value **general** channel has been updated to {input.id}")
            case default:
                await interaction.followup.send("""**Config options**: 
• lobby #channel
• agelog #channel
• modlobby #channel
• general #channel
""")
    @app_commands.command(name="welcome", description="**CONFIG COMMAND**: changes welcome message for when /approve is used")
    @commands.has_permissions(manage_guild=True)
    async def welcome(self, interaction: discord.Interaction, message: str):
        await interaction.response.defer(ephemeral=True)
        await configer.welcome(interaction.guild.id,  interaction,"welcome", message)

async def setup(bot: commands.Bot):
    await bot.add_cog(config(bot))

session.commit()