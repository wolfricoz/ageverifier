import logging

from sqlalchemy import Select, delete, func

from databases.current import DenialReasons
from databases.exceptions.CommitError import CommitError
from databases.transactions.DatabaseTransactions import DatabaseTransactions
from databases.transactions.ServerTransactions import ServerTransactions
from resources.data.config_variables import DEFAULT_DENIAL_REASONS


class DenialReasonTransactions(DatabaseTransactions) :
	"""A server's denial reason presets (classes.denialreasons sends them to the member).

	Every read and write is scoped to a guild, so another server's preset id matches nothing.
	A guild without presets is given DEFAULT_DENIAL_REASONS the first time they are read.
	"""

	def get_for_guild(self, guild_id: int) -> list[DenialReasons] :
		"""The guild's presets in the order they were added, seeding the defaults when there are none."""
		reasons = self._get_all(guild_id)
		if reasons :
			return reasons
		self._seed_defaults(guild_id)
		return self._get_all(guild_id)

	def get(self, guild_id: int, reason_id: int) -> DenialReasons | None :
		with self.createsession() as session :
			return session.scalar(Select(DenialReasons).where(DenialReasons.id == reason_id, DenialReasons.guild == guild_id))

	def count(self, guild_id: int) -> int :
		with self.createsession() as session :
			return session.scalar(Select(func.count(DenialReasons.id)).where(DenialReasons.guild == guild_id))

	def label_taken(self, guild_id: int, label: str, exclude_id: int = None) -> bool :
		"""Whether another of the guild's presets already uses this label (compared without case)."""
		with self.createsession() as session :
			query = Select(DenialReasons.id).where(DenialReasons.guild == guild_id,
			                                       func.lower(DenialReasons.label) == label.strip().lower())
			if exclude_id is not None :
				query = query.where(DenialReasons.id != exclude_id)
			return session.scalar(query.limit(1)) is not None

	def add(self, guild_id: int, label: str, message: str) -> DenialReasons :
		self._ensure_server(guild_id)
		with self.createsession() as session :
			reason = DenialReasons(guild=guild_id, label=label.strip(), message=message.strip())
			session.add(reason)
			session.flush()
			self.commit(session)
			logging.info(f"[DenialReasons] added preset {reason.id} in {guild_id}")
			return reason

	def update(self, guild_id: int, reason_id: int, label: str, message: str) -> bool :
		with self.createsession() as session :
			reason = session.scalar(Select(DenialReasons).where(DenialReasons.id == reason_id, DenialReasons.guild == guild_id))
			if reason is None :
				return False
			reason.label = label.strip()
			reason.message = message.strip()
			self.commit(session)
			return True

	def remove(self, guild_id: int, reason_id: int) -> bool :
		with self.createsession() as session :
			result = session.execute(delete(DenialReasons).where(DenialReasons.id == reason_id, DenialReasons.guild == guild_id))
			self.commit(session)
			return result.rowcount > 0

	def reset(self, guild_id: int) -> list[DenialReasons] :
		"""Replaces the guild's presets with the defaults."""
		with self.createsession() as session :
			session.execute(delete(DenialReasons).where(DenialReasons.guild == guild_id))
			self.commit(session)
		return self.get_for_guild(guild_id)

	def _get_all(self, guild_id: int) -> list[DenialReasons] :
		with self.createsession() as session :
			return list(session.scalars(Select(DenialReasons)
			                            .where(DenialReasons.guild == guild_id)
			                            .order_by(DenialReasons.id)).all())

	def _seed_defaults(self, guild_id: int) :
		self._ensure_server(guild_id)
		with self.createsession() as session :
			session.add_all(DenialReasons(guild=guild_id, label=label, message=message)
			                for label, message in DEFAULT_DENIAL_REASONS)
			try :
				self.commit(session)
			except CommitError :
				# Two reads seeded at once; the unique label index kept the first set.
				logging.info(f"[DenialReasons] defaults for {guild_id} were already seeded")

	@staticmethod
	def _ensure_server(guild_id: int) :
		# The hourly sync may not have recorded a guild that just added the bot.
		if ServerTransactions().get(guild_id) is None :
			ServerTransactions().add(guild_id, reload=False)
