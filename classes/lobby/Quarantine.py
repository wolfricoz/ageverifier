"""The QUARANTINE join fail action: a role given to members who fail a join requirement, taken off after a set time.

Nothing is stored per member. The quarantine starts when the member joins, so the release time is their join time
plus QUARANTINE_HOURS, and a task every 10 minutes releases every member of the role whose time is up. That keeps it working
across restarts, but it also means the role should only be used for this: a member staff give it to by hand is released
on the next run once they've been in the server longer than the duration.
"""
import logging
from datetime import UTC, datetime, timedelta

import discord
from discord.ext import commands

from classes.permissions_notice import PermissionNotice
from databases.transactions.ConfigData import ConfigData
from resources.data.config_variables import DEFAULT_QUARANTINE_HOURS, MAX_QUARANTINE_HOURS, QUARANTINE_HOURS_KEY, \
	QUARANTINE_ROLE_KEY


def quarantine_hours(guild_id: int) -> int :
	"""The configured duration in hours, falling back to the default when it is unset or not a valid number."""
	value = ConfigData().get_key_or_none(guild_id, QUARANTINE_HOURS_KEY)
	try :
		hours = int(value)
	except (TypeError, ValueError) :
		return DEFAULT_QUARANTINE_HOURS
	return min(max(hours, 1), MAX_QUARANTINE_HOURS)


def quarantine_role(guild: discord.Guild) -> discord.Role | None :
	"""The configured quarantine role, or None when it is unset or was deleted."""
	role_id = ConfigData().get_channel_id(guild.id, QUARANTINE_ROLE_KEY)
	if role_id is None :
		return None
	return guild.get_role(role_id)


async def apply_quarantine(member: discord.Member) -> bool :
	"""Gives the member the quarantine role. Returns False when no role is set or Discord refused it."""
	role = quarantine_role(member.guild)
	if role is None :
		logging.info(f"Quarantine: no quarantine role set in {member.guild.id}, only logging {member.id}.")
		return False
	try :
		await member.add_roles(role, reason="Failed a join requirement")
	except discord.Forbidden :
		await PermissionNotice.notify(member.guild, missing=["manage_roles"],
		                              purpose=f"give the @{role.name} quarantine role to members who fail a join requirement")
		return False
	except discord.HTTPException as e :
		logging.warning(f"Quarantine: could not add role {role.id} to {member.id} in {member.guild.id}: {e}")
		return False
	return True


def is_due(member: discord.Member, hours: int, now: datetime) -> bool :
	"""Whether the member has served their quarantine. A member without a join time is released."""
	if member.joined_at is None :
		return True
	return member.joined_at.astimezone(UTC) + timedelta(hours=hours) <= now


async def release_expired(bot: commands.Bot) -> int :
	"""Takes the quarantine role off members whose time is up, in every server that has one set.
	This doesn't check the fail action, so members still get released after a server switches away from QUARANTINE.
	Returns the number of members released."""
	now = datetime.now(UTC)
	released = 0
	for guild in bot.guilds :
		role = quarantine_role(guild)
		if role is None :
			continue
		hours = quarantine_hours(guild.id)
		for member in list(role.members) :
			if not is_due(member, hours, now) :
				continue
			try :
				await member.remove_roles(role, reason=f"Quarantine of {hours} hour(s) ended")
				released += 1
			except discord.Forbidden :
				await PermissionNotice.notify(guild, missing=["manage_roles"],
				                              purpose=f"remove the @{role.name} quarantine role when it runs out")
				# Every other member would fail the same way.
				break
			except discord.HTTPException as e :
				logging.warning(f"Quarantine: could not remove role {role.id} from {member.id} in {guild.id}: {e}")
	return released
