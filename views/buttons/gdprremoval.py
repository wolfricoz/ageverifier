import asyncio
import logging

import discord
from discord_py_utilities.messages import send_message, send_response

from classes.gdpr import pending_removal_date
from classes.support.queue import Queue
from databases.exceptions.KeyNotFound import KeyNotFound
from databases.transactions.ConfigData import ConfigData
from databases.transactions.LoggedMessageTransactions import LoggedMessageTransactions
from databases.transactions.UserTransactions import UserTransactions


class GDPRRemoval(discord.ui.View) :
	def __init__(self) :
		super().__init__(timeout=None)

	@discord.ui.button(label="I want my data removed", style=discord.ButtonStyle.danger, custom_id="remove")
	async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button) :
		# Delete first, then report: the removal date can only be read back once deleted_at is set.
		if UserTransactions().soft_delete(interaction.user.id, "Deleted By User (GDPR)") is False :
			await send_response(interaction, "No data found for you, so there is nothing to remove.", ephemeral=True)
			await self.disable_buttons(interaction)
			return
		removal_date = pending_removal_date(interaction.user.id)
		# ephemeral: the prompt this button hangs off is ephemeral, but a component response is a
		# new message - without this the reply announces the user's removal request to the channel.
		await send_response(interaction,
		                    f"Thank you, your data is hidden now.\n"
		                    f"It will be permanently removed on or shortly after {removal_date}.\n"
		                    f"-# Submitting your date of birth again before then will cancel the removal; we will ask you to confirm first.",
		                    ephemeral=True)

		embed = discord.Embed(
			title="A user has requested data removal!",
			description=f"{interaction.user.mention} has requested that all their data be removed from the bot. As a result, we can no longer guarantee their age. The bot will automatically remove their entries from your log channels."
		)
		embed.add_field(
			name="What should I do?",
			value="We strongly recommend returning the member to the lobby using `/lobby returnlobby` or removing them from your server."
		)
		embed.set_footer(text="GDPR Right to Erasure Request")
		await self.disable_buttons(interaction)
		tracked = await self.delete_tracked_messages(interaction)
		scan_history = tracked == 0
		if scan_history :
			logging.info(f"[GDPR] No tracked messages for {interaction.user.id}, falling back to a history scan.")
		for guild in interaction.client.guilds:
			await asyncio.sleep(0)
			if scan_history :
				await self.delete_lobby_entry(interaction, guild)
			if interaction.user in guild.members:
				try:
					mod_lobby = guild.get_channel(ConfigData().get_key_int(guild.id, "approval_channel"))
					await send_message(mod_lobby, embed=embed)
				except KeyNotFound:
					pass
				except discord.Forbidden:
					await send_message(guild.owner, embed=embed)

	async def disable_buttons(self, interaction, update=True,) :
		"""disables buttons"""
		for child in self.children :
			if child.custom_id in ["reactivate_buttons", "store_dob_left"] :
				continue
			child.disabled = True

		if not update :
			return
		try :
			await interaction.message.edit(view=self)
		except discord.NotFound :
			# The request message was already removed; nothing left to disable (AGEVERIFIER-FR).
			pass

	LOG_CHANNEL_KEYS = ("age_log", "reverify_age_log", "verification_failure_log", "approval_channel")

	@staticmethod
	def mentions_user(message: discord.Message, user_id: int) -> bool :
		"""Whether a message refers to the user, in its content or anywhere in its embeds.

		Embeds matter because the ID check posts put the user id in the embed footer rather than
		the message body, so a content-only check walks straight past them.
		"""
		needle = str(user_id)
		if needle in message.content :
			return True
		for embed in message.embeds :
			parts = [embed.title, embed.description, embed.footer.text if embed.footer else None]
			parts += [field.name for field in embed.fields]
			parts += [field.value for field in embed.fields]
			if any(needle in part for part in parts if part) :
				return True
		return False

	async def delete_tracked_messages(self, interaction: discord.Interaction) -> int :
		"""Deletes the messages recorded in logged_messages for this user, by id.

		This is the fast path, and the only one for anything the bot posted after the table was
		introduced: no history scan, one delete per known message.
		"""
		tracked = LoggedMessageTransactions().get_for_user(interaction.user.id)
		for entry in tracked :
			guild = interaction.client.get_guild(entry.guild)
			channel = guild.get_channel(entry.channel) if guild else None
			if channel is None :
				continue
			try :
				message = await channel.fetch_message(entry.message)
			except (discord.NotFound, discord.Forbidden) as e :
				# Already gone, or we lost access. Either way there is nothing left to delete.
				logging.info(f"[GDPR] Tracked {entry.type} message {entry.message} unavailable: {e}")
				continue
			logging.info(f"[GDPR] Deleting tracked {entry.type} message in {guild.name}")
			Queue().add(message.delete())
		LoggedMessageTransactions().delete_for_user(interaction.user.id)
		return len(tracked)

	async def delete_lobby_entry(self, interaction: discord.Interaction, guild: discord.Guild):
		"""Legacy history scan, for messages posted before logged_messages existed.

		Only reached when a user has no tracked messages at all. It is the expensive path - a
		full history read of four channels - so it exists purely so removals still reach data
		the bot posted before it started recording message ids.
		"""
		# Note: the caller deliberately runs this for every guild the bot is in, not just the ones
		# the user is currently a member of - their entries outlive them leaving, and those are
		# exactly the ones a removal has to reach.
		for key in self.LOG_CHANNEL_KEYS :
			# get_key_int_or_zero rather than ConfigData().get_channel: get_channel DMs the guild
			# owner a "channel not set" nag, which across four keys and every guild would spam
			# owners on every single removal.
			channel = guild.get_channel(ConfigData().get_key_int_or_zero(guild.id, key))
			if channel is None :
				continue
			try:
				# Future Improvement: [PERF] history(limit=None) scans the entire channel history every time, now across four channels. Track the message id at log time so you can delete it directly.
				async for message in channel.history(limit=None):
					# Only ever delete the bot's own posts. approval_channel carries staff
					# discussion, and sweeping that on a user id would delete their conversation.
					if message.author.id != interaction.client.user.id :
						continue
					if self.mentions_user(message, interaction.user.id):
						logging.info(f"[GDPR] Deleting {key} message in {guild.name}")
						Queue().add(message.delete())
			except discord.Forbidden:
				logging.warning(f"[GDPR] Cannot read {key} in {guild.name}, entries there were left in place.")

