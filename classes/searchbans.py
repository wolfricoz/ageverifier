import logging


import discord

from databases.controllers.TimersTransactions import TimersTransactions


async def remove(member: discord.Member, role, timer):
    await member.remove_roles(role)
    TimersTransactions().remove_timer(timer.id)
    logging.debug(f"Removed searchban from {member.name}")
