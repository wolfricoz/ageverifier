"""Staff notes on members, shown on the approval message."""
import logging

import discord
from discord import app_commands
from discord.ext import commands
from discord_py_utilities.messages import send_response

from classes.membernotes import EMBED_FIELD_LIMIT
from databases.transactions.MemberNoteTransactions import MemberNoteTransactions
from resources.data.config_variables import MAX_NOTE_LENGTH

# Discord's limit on fields in one embed.
MAX_LISTED_NOTES = 25


@app_commands.guild_only()
class Notes(commands.GroupCog, name="notes", description="Commands for keeping staff notes on members.") :
	"""
	Commands for keeping staff notes on members.
	Notes stay with the member in your server, also when they leave and rejoin, so context carries over between moderators.
	The newest notes are shown on the member's approval message; turn this off with `/config approval_toggles staff_notes`.
	Notes are only visible to your server's staff and are deleted together with the member's record.
	"""

	def __init__(self, bot: commands.Bot) :
		self.bot = bot

	@app_commands.command(name="add", description="Adds a staff note to a member.")
	@app_commands.checks.has_permissions(manage_messages=True)
	async def add(self, interaction: discord.Interaction, user: discord.User,
	              note: app_commands.Range[str, 1, MAX_NOTE_LENGTH]) :
		"""
		Adds a note to a member that other staff in this server will see on their approval message and with `/notes list`.
		Notes are kept when the member leaves and rejoins.

		**Permissions:**
		- You'll need the `Manage Messages` permission to use this command.
		"""
		entry = MemberNoteTransactions().add(interaction.guild.id, user.id, interaction.user.id, note)
		await send_response(interaction, f"Note #{entry.id} added to {user.mention}.", ephemeral=True)

	@app_commands.command(name="list", description="Shows the staff notes on a member.")
	@app_commands.checks.has_permissions(manage_messages=True)
	async def list(self, interaction: discord.Interaction, user: discord.User) :
		"""
		Shows this server's notes on a member, newest first, with who wrote them and when.
		Use the note number with `/notes remove` to delete one.

		**Permissions:**
		- You'll need the `Manage Messages` permission to use this command.
		"""
		total = MemberNoteTransactions().count_for_member(interaction.guild.id, user.id)
		if total == 0 :
			await send_response(interaction, f"There are no notes on {user.mention}.", ephemeral=True)
			return
		notes = MemberNoteTransactions().get_for_member(interaction.guild.id, user.id, limit=MAX_LISTED_NOTES)
		embed = discord.Embed(title=f"Staff notes on {user.name}", description=f"{user.mention} ({user.id})")
		for note in notes :
			when = discord.utils.format_dt(note.created_at, style="R") if note.created_at else "unknown date"
			embed.add_field(name=f"#{note.id}",
			                value=f"{note.text}\n-# by <@{note.author}>, {when}"[:EMBED_FIELD_LIMIT],
			                inline=False)
		if total > len(notes) :
			embed.set_footer(text=f"+{total - len(notes)} older notes not shown")
		await send_response(interaction, " ", embed=embed, ephemeral=True)

	@app_commands.command(name="remove", description="Removes a staff note.")
	@app_commands.checks.has_permissions(manage_messages=True)
	async def remove(self, interaction: discord.Interaction, note_id: int) :
		"""
		Removes a note by its number, as shown by `/notes list`. Only notes written in this server can be removed.

		**Permissions:**
		- You'll need the `Manage Messages` permission to use this command.
		"""
		if not MemberNoteTransactions().remove(interaction.guild.id, note_id) :
			await send_response(interaction, f"Note #{note_id} was not found in this server.", ephemeral=True)
			return
		logging.info(f"[MemberNotes] {interaction.user.id} removed note {note_id} in {interaction.guild.id}")
		await send_response(interaction, f"Note #{note_id} removed.", ephemeral=True)


async def setup(bot) :
	"""Adds cog to the bot"""
	await bot.add_cog(Notes(bot))
