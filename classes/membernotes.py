"""Staff notes on a member, as shown on the approval message (STR-83)."""
import discord

from databases.current import MemberNotes

# Discord rejects an embed whose field value is longer than this.
EMBED_FIELD_LIMIT = 1024


def format_note(note: MemberNotes) -> str :
	when = discord.utils.format_dt(note.created_at, style="R") if note.created_at else "unknown date"
	return f"• {note.text} — <@{note.author}>, {when}"


def format_notes(notes: list[MemberNotes] | None, total: int = None) -> str | None :
	"""
	Formats the newest notes for the approval embed.

	:param notes: the notes to show, newest first.
	:param total: how many notes the member has in this guild, when more exist than are shown.
	:return: the field value, or None if there are no notes so the field is skipped.
	"""
	if not notes :
		return None
	total = max(total or 0, len(notes))
	more = f"\n+{total - len(notes)} more, see `/notes list`" if total > len(notes) else ""
	value = "\n".join(format_note(note) for note in notes)
	if len(value) + len(more) > EMBED_FIELD_LIMIT :
		# Shortened rather than dropped, so staff still see that notes exist and where to read them.
		more = more or "\nsee `/notes list` for the full notes"
		value = value[:EMBED_FIELD_LIMIT - len(more) - 1] + "…"
	return value + more
