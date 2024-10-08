import os

import discord
from discord import app_commands
from discord.ext import commands

from classes.databaseController import ConfigData


def check_dev(userid):
    if int(userid) == int(os.getenv("DEVELOPER")):
        return True

def check_admin(user: discord.Member):
    adminroles = ConfigData().get_key(user.guild.id, 'admin')
    user_roles = [x.id for x in user.roles]
    return any(x in adminroles for x in user_roles)


def check_roles():
    async def pred(ctx):
        modroles = ConfigData().get_key(ctx.guild.id, 'mod')
        adminroles = ConfigData().get_key(ctx.guild.id, 'admin')
        user_roles = [x.id for x in ctx.author.roles]
        return any(x in adminroles for x in user_roles) or any(x in modroles for x in user_roles)

    return commands.check(pred)


def check_roles_admin():
    async def pred(ctx):
        adminroles = ConfigData().get_key(ctx.guild.id, 'admin')
        user_roles = [x.id for x in ctx.author.roles]
        return any(x in adminroles for x in user_roles)

    return commands.check(pred)


def check_app_roles():
    async def pred(interaction: discord.Interaction):
        if check_dev(interaction.user.id):
            return True
        modroles = ConfigData().get_key(interaction.guild.id, 'mod')
        adminroles = ConfigData().get_key(interaction.guild.id, 'admin')
        user_roles = [x.id for x in interaction.user.roles]
        return any(x in adminroles for x in user_roles) or any(x in modroles for x in user_roles)

    return app_commands.check(pred)


def check_app_roles_admin():
    async def pred(interaction):
        if check_dev(interaction.user.id):
            return True
        adminroles = ConfigData().get_key(interaction.guild.id, 'admin')
        user_roles = [x.id for x in interaction.user.roles]
        return any(x in adminroles for x in user_roles)

    return app_commands.check(pred)
