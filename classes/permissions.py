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
