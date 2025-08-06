import logging

import discord

from classes.jsonmaker import Configer
from discord_py_utilities.messages import send_message
from classes.support.queue import Queue


async def blacklist_check(guild: discord.Guild, log: discord.TextChannel) -> bool:

    if await Configer.is_blacklisted(guild.id):
        logging.info(f"Leaving {guild.name} because it is blacklisted")
        Queue().add(send_message(log, f"Leaving {guild}({guild.id}) because it is blacklisted"))
        await guild.leave()
        # await log.send(f"[DEV MODE] Leaving disabled for testing")
        return True
    if await Configer.is_user_blacklisted(guild.owner.id):
        logging.info(f"Leaving {guild.name} because the {guild.owner.name}({guild.owner.id}) is blacklisted")
        Queue().add(send_message(log, f"Leaving {guild}({guild.id}) because the {guild.owner.name}({guild.owner.id}) is blacklisted"))
        await Configer.add_to_blacklist(guild.id)
        # await log.send(f"[DEV MODE] Leaving disabled for testing")
        await guild.leave()
        return True
    return False
