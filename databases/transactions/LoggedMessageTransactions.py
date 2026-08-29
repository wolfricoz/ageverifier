import logging

import discord
from sqlalchemy import Select, delete

from databases.current import LoggedMessage
from databases.enums.loggedmessagetype import LoggedMessageType
from databases.transactions.DatabaseTransactions import DatabaseTransactions
from databases.transactions.UserTransactions import UserTransactions


class LoggedMessageTransactions(DatabaseTransactions) :
	"""Tracks the messages the bot posts that contain a user's age or date of birth.

	A GDPR removal deletes those messages from the guilds they were posted in. Recording them
	here as they are sent means the removal can delete them by id instead of scanning the full
	history of four log channels in every guild the bot is in.
	"""

	def track(self, message: discord.Message | None, user_id: int, message_type: LoggedMessageType) :
		"""Records a sent message so a later removal can delete it directly.

		Tolerates a missing message: send_message returns None when the bot was not allowed to
		post, and there is nothing to clean up in that case. Never raises - failing to record a
		message must not break the verification flow that was posting it.
		"""
		if message is None or message.guild is None :
			return None
		try :
			with self.createsession() as session :
				# Same guard the other tables use: the uid foreign key needs a user row, and the
				# approval post goes out before the date of birth is stored.
				if not UserTransactions().user_exists(user_id) :
					UserTransactions().add_user_empty(user_id, True)
				entry = LoggedMessage(
					uid=user_id,
					guild=message.guild.id,
					channel=message.channel.id,
					message=message.id,
					type=message_type,
				)
				session.add(entry)
				self.commit(session)
				return entry
		except Exception as e :
			logging.warning(f"[LoggedMessage] Could not track {message_type} message for {user_id}: {e}")
			return None

	def get_for_user(self, user_id: int) -> list[LoggedMessage] :
		"""Every tracked message for a user, across all guilds."""
		with self.createsession() as session :
			return list(session.scalars(Select(LoggedMessage).where(LoggedMessage.uid == user_id)).all())

	def delete_for_user(self, user_id: int) -> int :
		"""Drops a user's tracked rows once their messages have been dealt with."""
		with self.createsession() as session :
			result = session.execute(delete(LoggedMessage).where(LoggedMessage.uid == user_id))
			self.commit(session)
			logging.info(f"[LoggedMessage] Removed {result.rowcount} tracked messages for {user_id}")
			return result.rowcount

	def delete_message(self, message_id: int) -> None :
		"""Drops a single tracked row, for when its message is gone."""
		with self.createsession() as session :
			session.execute(delete(LoggedMessage).where(LoggedMessage.message == message_id))
			self.commit(session)
