"""Developer-only slash commands live in the developers' server only.

Registered globally they showed up in every server owner's command picker (about 20 [DEV] commands), even
though they refuse anyone but the developer. SUPPORTGUILD is the developers' server; without it set (local
tests) the commands stay global so they can still be reached.
"""
import os

import discord
from discord import app_commands


def dev_guild() -> discord.Object | None :
	guild_id = os.getenv("SUPPORTGUILD", "").strip()
	return discord.Object(id=int(guild_id)) if guild_id.isnumeric() else None


def dev_guild_only(command) :
	"""Decorator for a single top-level [DEV] command in a cog that also has public commands.
	Put it above @app_commands.command."""
	guild = dev_guild()
	return app_commands.guilds(guild)(command) if guild else command


async def sync_dev_guild(bot: discord.Client) :
	"""tree.sync() only syncs global commands; the developer server's commands need their own sync."""
	guild = dev_guild()
	if guild is not None :
		await bot.tree.sync(guild=guild)
