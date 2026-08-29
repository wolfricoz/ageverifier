# This class is a collection of multiple tools, which can be called by the 'run' function.
import asyncio
import logging
import re

import discord

from databases.enums.loggedmessagetype import LoggedMessageType
from databases.transactions.ConfigData import ConfigData
from databases.transactions.LoggedMessageTransactions import LoggedMessageTransactions
from databases.transactions.UserTransactions import UserTransactions
from views.buttons.gdprremoval import GDPRRemoval


class Toolbox():

	TOOLS_LIST = {
		"View guilds without ban permissions": "ListGuildsWithoutBanPerms",
		"Backfill old log messages": "BackfillLoggedMessages"
	}

	async def run(self, interaction: discord.Interaction, tool: str, *args, **kwargs):
		# We get the function
		f = getattr(self, tool)
		if not f:
			raise AttributeError("Tool doesn't exist")
		# We fill in potential arguments, run the function and return the output. All functions must be async.
		return await f(interaction, *args, **kwargs)

	async def ListGuildsWithoutBanPerms(self, interaction: discord.Interaction, *args, **kwargs):
		"""
		"""
		missing = []
		# test for permission
		for guild in interaction.client.guilds:
			if guild.me.guild_permissions.ban_members:
				continue
			missing.append(guild)
		result = "Missing ban permissions: \n" + "\n".join([f"{g.name} ({g.id})" for g in missing])
		return result

	async def BackfillLoggedMessages(self, interaction: discord.Interaction, *args, **kwargs):
		"""
		Records the log messages that predate the logged_messages table, so a GDPR removal can
		find them. Reads full channel history, so it takes a while.
		kwargs: dry_run (defaults to True), guild (a single guild instead of all of them).
		"""
		dry_run = kwargs.get("dry_run", True)
		guild = kwargs.get("guild")
		guilds = [guild] if guild else list(interaction.client.guilds)
		bot_id = interaction.client.user.id
		# Cached per run: user id -> tracked message ids, or None when the user is already gone.
		known = {}
		scanned = tracked = skipped = 0

		for target in guilds:
			# Same channels the GDPR removal sweeps, taken from there so the two can't drift.
			for key in GDPRRemoval.LOG_CHANNEL_KEYS:
				channel = target.get_channel(ConfigData().get_key_int_or_zero(target.id, key))
				if channel is None:
					continue
				try:
					async for message in channel.history(limit=None):
						await asyncio.sleep(0)
						if message.author.id != bot_id:
							continue
						scanned += 1
						if self.record_message(message, known, dry_run):
							tracked += 1
						else:
							skipped += 1
				except discord.Forbidden:
					logging.warning(f"[Backfill] Cannot read {key} in {target.name}, skipped.")
				except Exception as e:
					logging.error(f"[Backfill] Failed on {key} in {target.name}: {e}", exc_info=True)
			logging.info(f"[Backfill] {target.name}: {tracked} tracked, {scanned} scanned")

		logging.info(f"[Backfill] Finished: {tracked} tracked, {scanned} scanned, {skipped} skipped")
		return (f"{'**Dry run**, nothing was written. Pass dry_run=False to write.' if dry_run else '**Backfill complete**'}\n"
		        f"Guilds: {len(guilds)}\n"
		        f"Messages scanned: {scanned}\n"
		        f"{'Would record' if dry_run else 'Recorded'}: {tracked}\n"
		        f"Skipped: {skipped}")

	# Helpers for BackfillLoggedMessages, not tools in their own right.

	def record_message(self, message, known, dry_run):
		"""Tracks one old message. Returns True when it counted, False when it was skipped."""
		found = self.identify_message(message)
		if found is None:
			return False
		user_id, message_type = found

		if user_id not in known:
			if not UserTransactions().user_exists(user_id):
				# Already purged, so there is no removal left for this to serve. Tracking it would
				# also recreate the user row to satisfy the foreign key, undoing that deletion.
				known[user_id] = None
			else:
				known[user_id] = {entry.message for entry in
				                  LoggedMessageTransactions().get_for_user(user_id)}
		if known[user_id] is None or message.id in known[user_id]:
			return False

		if not dry_run:
			LoggedMessageTransactions().track(message, user_id, message_type)
		known[user_id].add(message.id)
		return True

	def identify_message(self, message):
		"""Works out who an old bot message is about and what kind it is, or None."""
		content = message.content or ""

		# The ID check embed has the user id in its footer, which beats anything in the body.
		for embed in message.embeds:
			footer = embed.footer.text if embed.footer else None
			if embed.title == "ID Check Required" and footer and footer.strip().isdigit():
				return int(footer.strip()), LoggedMessageType.ID_CHECK

		# Read the user out of its own field, never "any mention present": these posts also ping
		# the guild owner, and blaming them would make their removal delete someone else's post.
		match = re.search(r"userid:\s*<@!?(\d+)>", content)
		if match:
			return int(match.group(1)), LoggedMessageType.ID_CHECK
		match = re.search(r"[Cc]ustom idcheck for\s*<@!?(\d+)>", content)
		if match:
			return int(match.group(1)), LoggedMessageType.ID_CHECK

		# Both of these sit in age_log, so they're told apart by shape and not by channel.
		match = re.search(r"UID:\s*(\d+)", content)
		if match:
			if content.lstrip().startswith("USER "):
				return int(match.group(1)), LoggedMessageType.AGE_LOG
			if "Age:" in content:
				return int(match.group(1)), LoggedMessageType.LOBBY_LOG

		# An approval post opens with the member's mention and puts the rest in an embed.
		if message.embeds:
			match = re.match(r"^\s*<@!?(\d+)>", content)
			if match:
				return int(match.group(1)), LoggedMessageType.APPROVAL

		return None
