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

class config(commands.GroupCog, name="remrole"):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="add", description="**CONFIG COMMAND**: Adds role to list that will be removed from user when /approve is used")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def radd(self, interaction: discord.Interaction, role: discord.Role):
        await interaction.response.defer(ephemeral=True)
        await configer.addrole(interaction.guild.id, interaction, role.id, "remrole")

    @app_commands.command(name="remove", description="**CONFIG COMMAND**: Removes role from list that will be removed from user when /approve is used")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def rrem(self, interaction: discord.Interaction, role: discord.Role):
        await interaction.response.defer( ephemeral=True)
        try:
            await configer.remrole(interaction.guild.id, interaction, role.id, "remrole")
            await interaction.followup.send(f"{Role} was removed from config.")
        except:
            await interaction.followup.send(f"{Role} was not in the list.")

async def setup(bot: commands.Bot):
    await bot.add_cog(config(bot))

session.commit()