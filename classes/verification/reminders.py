import logging
import os
from datetime import datetime, timedelta

import discord
from discord.ext import commands

from classes.access import AccessControl
from classes.helpers import fetch_member
from classes.support.queue import Queue
from databases.current import WebsiteData
from databases.transactions.ConfigData import ConfigData
from databases.transactions.WebsiteDataTransactions import WebsiteDataTransactions
from resources.data.config_variables import MAX_VERIFICATION_REMINDER_MINUTES, VERIFICATION_KEY, \
	VERIFICATION_REMINDER_KEY, VerificationMethods
from views.buttons.websitebutton import WebsiteButton


def reminder_minutes(guild_id: int) -> int :
	"""The guild's reminder delay in minutes, 0 when the reminder is off or the value is unusable."""
	try :
		minutes = ConfigData().get_key_int_or_zero(guild_id, VERIFICATION_REMINDER_KEY)
	except (ValueError, TypeError) :
		logging.warning(f"Invalid {VERIFICATION_REMINDER_KEY} for guild {guild_id}, treating it as disabled.")
		return 0
	return max(0, min(minutes, MAX_VERIFICATION_REMINDER_MINUTES))


def still_in_lobby(member: discord.Member) -> bool :
	"""
	Whether the member still holds a lobby role. A member who got verified some other way
	(staff approval, Discord verification) loses these, while their website link stays unfinished.
	Servers without lobby roles configured can't be checked, so the link state alone decides.
	"""
	lobby_roles = (ConfigData().get_key_or_none(member.guild.id, "server_join_role") or []) + (
			ConfigData().get_key_or_none(member.guild.id, "verification_remove_role") or [])
	if not lobby_roles :
		return True
	return any(role.id in lobby_roles for role in member.roles)


async def send_reminder(member: discord.Member, url: str) :
	try :
		await member.send(
			f"You opened the age verification page for **{member.guild.name}** but didn't finish. "
			f"Your verification link is still valid, use the button below to pick up where you left off.",
			view=WebsiteButton(url))
	except (discord.Forbidden, discord.HTTPException) as e :
		logging.info(f"Unable to send the verification reminder to {member.id} in {member.guild.id}: {e}")


async def send_abandoned_reminders(bot: commands.Bot) -> int :
	"""
	Messages members of premium guilds who opened the online verification page but did not
	finish within the guild's configured time. Each link is reminded at most once: it is marked
	as reminded as soon as it is handled, including when the member can't be reached, so a
	member who left or has DMs closed isn't retried every run.
	Returns the number of reminders queued.
	"""
	access_control = AccessControl()
	if len(access_control.premium_guilds) < 1 :
		access_control.add_premium_guilds_to_list()

	website_base = os.getenv("DASHBOARD_URL")
	transactions = WebsiteDataTransactions()
	entries: list[WebsiteData] = transactions.get_abandoned(timedelta(minutes=MAX_VERIFICATION_REMINDER_MINUTES))
	now = datetime.now()
	sent = 0
	for entry in entries :
		# Checked every run, not marked: a guild that becomes premium or turns the reminder on
		# later still gets reminders for links that are recent enough.
		if not access_control.is_premium(entry.gid) :
			continue
		minutes = reminder_minutes(entry.gid)
		if minutes == 0 or entry.opened > now - timedelta(minutes=minutes) :
			continue

		transactions.set_reminded(entry.uuid)
		guild = bot.get_guild(entry.gid)
		if guild is None :
			continue
		if ConfigData().get_key(guild.id, VERIFICATION_KEY, VerificationMethods.WEBSITE) != VerificationMethods.WEBSITE :
			continue
		member = await fetch_member(guild, entry.uid)
		if member is None or not still_in_lobby(member) :
			continue

		url = f"{website_base}/ageverifier/verification/{entry.uid}/{entry.gid}/{entry.uuid}"
		Queue().add(send_reminder(member, url), priority=0)
		sent += 1
	logging.info(f"Queued {sent} abandoned verification reminders.")
	return sent
