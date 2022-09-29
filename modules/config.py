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
Session = sessionmaker(bind=db.engine)
session = Session()

class config(commands.GroupCog, name="config"):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
    #TODO: Change this into 2 commands, config channel and config role
    @app_commands.command(name="role")
    @commands.has_permissions(manage_guild=True)
    async def crole(self, interaction: discord.Interaction, option :str ="default", input:  discord.Role = None):
        print(interaction.guild.id)
        c = session.query(db.config).filter_by(guild=interaction.guild.id).first()
        p = session.query(db.permissions).filter_by(guild=interaction.guild.id).first()
        match option:
            case "lobby":
                c.lobby = input.id
                session.commit()
                await interaction.send(f"Value **lobby** channel has been updated to {input.id}")
            case "agelog":
                c.agelog = input.id
                session.commit()
                await interaction.send(f"Value **agelog** channel has been updated to {input.id}")
            case "modlobby":
                c.modlobby = input.id
                session.commit()
                await interaction.send(f"Value **modlobby** channel has been updated to {input.id}")
            case "general":
                c.general = input.id
                session.commit()
                await interaction.send(f"Value **general** channel has been updated to {input.id}")
            case "admin":
                p.admin = input.id
                session.commit()
                await interaction.send(f"Value **admin** role has been updated to {input.id}")
            case "mod":
                p.mod = input.id
                session.commit()
                await interaction.send(f"Value **mod** role has been updated to {input.id}")
            case "trial":
                p.trial = input.id
                session.commit()
                await interaction.send(f"Value **trial** role has been updated to {input.id}")
            case "lobbystaff":
                p.lobbystaff = input.id
                session.commit()
                await interaction.send(f"Value **lobbyteam** role has been updated to {input.id}")
            case default:
                await interaction.send("""**Config options**: 
• lobby #channel
• agelog #channel
• modlobby #channel
• general #channel
• admin @role
• mod @role
• trial @role
• lobbystaff @role""")

    @app_commands.command(name="channel")
    @commands.has_permissions(manage_guild=True)
    async def cchannel(self, interaction: discord.Interaction, option :str="default", input:  discord.Role = None):
        print(interaction.guild.id)
        c = session.query(db.config).filter_by(guild=interaction.guild.id).first()
        p = session.query(db.permissions).filter_by(guild=interaction.guild.id).first()
        match option:
            case "lobby":
                c.lobby = input.id
                session.commit()
                await interaction.send(f"Value **lobby** channel has been updated to {input.id}")
            case "agelog":
                c.agelog = input.id
                session.commit()
                await interaction.send(f"Value **agelog** channel has been updated to {input.id}")
            case "modlobby":
                c.modlobby = input.id
                session.commit()
                await interaction.send(f"Value **modlobby** channel has been updated to {input.id}")
            case "general":
                c.general = input.id
                session.commit()
                await interaction.send(f"Value **general** channel has been updated to {input.id}")
            case "admin":
                p.admin = input.id
                session.commit()
                await interaction.send(f"Value **admin** role has been updated to {input.id}")
            case "mod":
                p.mod = input.id
                session.commit()
                await interaction.send(f"Value **mod** role has been updated to {input.id}")
            case "trial":
                p.trial = input.id
                session.commit()
                await interaction.send(f"Value **trial** role has been updated to {input.id}")
            case "lobbystaff":
                p.lobbystaff = input.id
                session.commit()
                await interaction.send(f"Value **lobbyteam** role has been updated to {input.id}")
            case default:
                await interaction.send("""**Config options**: 
• lobby #channel
• agelog #channel
• modlobby #channel
• general #channel
• admin @role
• mod @role
• trial @role
• lobbystaff @role""")

async def setup(bot: commands.Bot):
    await bot.add_cog(config(bot))

session.commit()