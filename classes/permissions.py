import os

import discord

from databases.transactions.ConfigData import ConfigData


def check_dev(userid):
    return int(userid) == int(os.getenv("DEVELOPER"))


def check_admin(user: discord.Member):
    adminroles = ConfigData().get_key(user.guild.id, 'admin')
    if not adminroles:
        return False
    user_roles = [x.id for x in user.roles]
    return any(x in adminroles for x in user_roles)
