import logging

from sqlalchemy import Select, delete, func

from databases.current import MemberNotes
from databases.transactions.DatabaseTransactions import DatabaseTransactions
from databases.transactions.ServerTransactions import ServerTransactions
from databases.transactions.UserTransactions import UserTransactions


class MemberNoteTransactions(DatabaseTransactions) :
	"""Staff notes on a member, per guild (classes.membernotes formats them for the approval message).

	Every read and delete is scoped to a guild: a note is only ever visible to, and removable by,
	the server that wrote it. Retention is handled by the foreign keys, see MemberNotes.
	"""

	def add(self, guild_id: int, user_id: int, author_id: int, text: str) -> MemberNotes :
		# Both foreign keys need their row: staff can note a member who never verified, and the
		# hourly sync may not have recorded a guild that just added the bot.
		if not UserTransactions().user_exists(user_id) :
			UserTransactions().add_user_empty(user_id, True)
		if ServerTransactions().get(guild_id) is None :
			ServerTransactions().add(guild_id, reload=False)
		with self.createsession() as session :
			note = MemberNotes(uid=user_id, guild=guild_id, author=author_id, text=text)
			session.add(note)
			session.flush()
			self.commit(session)
			# Ids only: the note text is the guild's and stays out of the logs.
			logging.info(f"[MemberNotes] {author_id} added note {note.id} on {user_id} in {guild_id}")
			return note

	def get_for_member(self, guild_id: int, user_id: int, limit: int = None) -> list[MemberNotes] :
		"""The guild's notes on a member, newest first."""
		with self.createsession() as session :
			query = (Select(MemberNotes)
			         .where(MemberNotes.guild == guild_id, MemberNotes.uid == user_id)
			         .order_by(MemberNotes.created_at.desc(), MemberNotes.id.desc()))
			if limit is not None :
				query = query.limit(limit)
			return list(session.scalars(query).all())

	def count_for_member(self, guild_id: int, user_id: int) -> int :
		with self.createsession() as session :
			return session.scalar(Select(func.count(MemberNotes.id))
			                      .where(MemberNotes.guild == guild_id, MemberNotes.uid == user_id))

	def count_for_user(self, user_id: int) -> int :
		"""Notes on a user across every guild, for /gdpr data. Only the number is ever shown to the user."""
		with self.createsession() as session :
			return session.scalar(Select(func.count(MemberNotes.id)).where(MemberNotes.uid == user_id))

	def remove(self, guild_id: int, note_id: int) -> bool :
		"""Deletes one note. Scoped to the guild, so another server's note id matches nothing."""
		with self.createsession() as session :
			result = session.execute(delete(MemberNotes).where(MemberNotes.id == note_id, MemberNotes.guild == guild_id))
			self.commit(session)
			return result.rowcount > 0
