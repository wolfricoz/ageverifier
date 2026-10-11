import logging
from datetime import datetime, timedelta
from typing import Optional
from uuid import uuid4

from sqlalchemy import Select, text

from databases.current import WebsiteData
from databases.transactions.DatabaseTransactions import DatabaseTransactions
from databases.transactions.UserTransactions import UserTransactions


class WebsiteDataTransactions(DatabaseTransactions) :
	"""
	Handles database transactions for the LobbyData model.
	"""

	def create(self, user_id: int, guild_id: int) -> str :
		"""
		Creates a new WebsiteData record.

		Returns:
				The newly created LobbyData object.
		"""
		with self.createsession() as session :
			# Ensure the user exists to prevent foreign key issues
			user = UserTransactions().get_user(user_id, session=session)
			if not user:
				UserTransactions().add_user_empty(user_id)
			# Create the WebsiteData entry
			uuid = uuid4().__str__()
			new_entry = WebsiteData(
				uuid=uuid,
				uid=user_id,
				gid=guild_id
			)
			session.add(new_entry)
			self.commit(session)
			logging.info(f"Created new lobby data for message_id: {user_id}.")
			return uuid

	def read(self, uuid: str, session = None) -> Optional[WebsiteData] :
		"""
		Retrieves a single WebsiteData entry by its message ID.

		Args:
				uuid: The ID of the Discord message.

		Returns:
				A LobbyData object or None if not found.
		"""
		if session :
			return session.scalar(
				Select(WebsiteData)
				.where(WebsiteData.uuid == str(uuid))
			)
		with self.createsession() as session :
			return session.scalar(
				Select(WebsiteData)
				.where(WebsiteData.uuid == str(uuid))
			)

		# def delete(self, uuid: str) -> bool:
		#     """
		#     Permanently deletes a LobbyData entry.
		#
		#     Args:
		#         uuid: The ID of the Discord message.
		#
		#     Returns:
		#         True if deletion was successful, False otherwise.
		#     """
		#     with self.createsession() as session:
		#         entry = self.read(uuid)
		#         if entry:
		#             session.delete(entry)
		#             self.commit(session)
		#             logging.info(f"Deleted lobby data for message_id: {uuid}.")
		#             return True
		#         logging.warning(f"Attempted to delete non-existent lobby data for message_id: {uuid}.")
		#         return False
		#

	def clean_table(self) :
		with self.createsession() as session :
			result = session.execute(text("DELETE FROM website_data WHERE created_date < NOW() - INTERVAL '90 DAYS'"))
			self.commit(session)
			return result

	def owner_mismatch(self, guid: str, user_id: int, guild_id: int) -> bool :
		"""
		Whether the link exists but was issued to another member or server. The verify routes call this
		before processing anything, so a submission on someone else's link has no side effects.
		An unknown guid is not a mismatch: set_verified already ignores those.
		"""
		with self.createsession() as session :
			entry = self.read(guid, session)
			if entry is None :
				return False
			if entry.uid != user_id or entry.gid != guild_id :
				logging.warning(f"Verification submitted on {guid} by {user_id} in {guild_id}, but it belongs to {entry.uid} in {entry.gid}.")
				return True
			return False

	def set_verified(self, guid, user_id) :
		with self.createsession() as session :
			entry = self.read(guid, session)
			if entry :
				if entry.uid != user_id :
					raise ValueError(f"User id {user_id} does not match {guid}.")

				entry.verified = datetime.now()
				self.commit(session)
				logging.info(f"Set verification for {guid} to True.")
				return True
			logging.warning(f"Attempted to set verification for {guid} to True, but entry not found.")

	def check(self, user_id: int, guild_id: int, retrieve: bool = True) -> bool | str :
		with self.createsession() as session :
			result = session.scalar(Select(WebsiteData).where(WebsiteData.uid == user_id, WebsiteData.gid == guild_id, WebsiteData.verified.is_(None)))

			if result and retrieve:
				return result.uuid
			if result:
				return True
			return False

	def set_opened(self, guid: str, user_id: int, guild_id: int) -> bool :
		"""
		Records the first time the member loaded the verification page. Later loads keep the
		original time, so the reminder counts from when they first saw the page.
		The ids are checked against the row so a guid cannot be marked for someone else.
		"""
		with self.createsession() as session :
			entry = self.read(guid, session)
			if not entry or entry.uid != user_id or entry.gid != guild_id :
				logging.warning(f"Attempted to mark {guid} as opened, but no matching entry was found.")
				return False
			if entry.opened is None :
				entry.opened = datetime.now()
				self.commit(session)
			return True

	def get_abandoned(self, max_age: timedelta) -> list[WebsiteData] :
		"""
		Returns links that were opened but never finished and have not been reminded yet.
		max_age bounds how far back to look, so links abandoned long before the reminder
		was enabled are not all messaged at once.
		"""
		with self.createsession() as session :
			return list(session.scalars(
				Select(WebsiteData).where(
					WebsiteData.opened.is_not(None),
					WebsiteData.opened >= datetime.now() - max_age,
					WebsiteData.verified.is_(None),
					WebsiteData.reminded.is_(None),
				)
			).all())

	def set_reminded(self, guid: str) -> bool :
		with self.createsession() as session :
			entry = self.read(guid, session)
			if not entry :
				return False
			entry.reminded = datetime.now()
			self.commit(session)
			return True
