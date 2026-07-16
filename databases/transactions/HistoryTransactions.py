import logging
from datetime import datetime

from sqlalchemy import Select, desc, text

from databases.current import JoinHistory
from databases.enums.joinhistorystatus import JoinHistoryStatus
from databases.transactions.DatabaseTransactions import DatabaseTransactions
from databases.transactions.UserTransactions import UserTransactions


# Assuming the following are defined elsewhere in your project
# from .database import DatabaseTransactions, db
# from .models import JoinHistory, JoinHistoryStatus

class JoinHistoryTransactions(DatabaseTransactions) :
	"""
	Handles all database transactions for the JoinHistory model.
	"""

	def get(self, uid: int, gid: int, session=None, latest=True) -> 'JoinHistory | None' :
		"""
		Retrieves a single JoinHistory entry by user ID and guild ID.

		Args:
				uid: The user's unique ID.
				gid: The guild's unique ID.

		Returns:
				A JoinHistory object or None if not found.
		"""
		if session :
			return session.scalar(
				Select(JoinHistory)
				.where(JoinHistory.uid == uid, JoinHistory.gid == gid)
				.order_by(JoinHistory.created_date)
				.limit(1)
			)
		with self.createsession() as session :
			return session.scalar(
				Select(JoinHistory)
				.where(JoinHistory.uid == uid, JoinHistory.gid == gid)
				.order_by(desc(JoinHistory.created_date))
				.limit(1)
			)

	def get_all_for_guild(self, gid: int) -> list['JoinHistory'] :
		"""
		Retrieves all JoinHistory entries for a specific guild.

		Args:
				gid: The guild's unique ID.

		Returns:
				A list of JoinHistory objects.
		"""
		with self.createsession() as session :
			return session.scalars(Select(JoinHistory).where(JoinHistory.gid == gid)).all()

	def get_all_for_user(self, uid: int) -> list['JoinHistory'] :
		"""
		Retrieves all JoinHistory entries for a specific user across all guilds.

		Args:
				uid: The user's unique ID.

		Returns:
				A list of JoinHistory objects.
		"""
		with self.createsession() as session :
			return session.scalars(Select(JoinHistory).where(JoinHistory.uid == uid)).all()

	def add(self, uid: int, gid: int, status: 'JoinHistoryStatus',
	        verification_date: datetime = None, message_id: int = None, new_record: bool = True,  created_at = None) -> 'JoinHistory' :
		"""
		Adds a new JoinHistory entry or updates an existing one.

		If an entry for the given uid and gid already exists, it will be updated
		with the new values. Otherwise, a new entry is created.

		Args:
				uid: The user's unique ID.
				gid: The guild's unique ID.
				status: The current join status of the user.
				verification_date: The date the user was verified, if applicable.
				message_id: The ID of the related verification message, if applicable.
				new_record: If true, a new entry will be created.

		Returns:
				The created or updated JoinHistory object.
		"""
		with self.createsession() as session :
			# Check if user exists:
			user = UserTransactions().get_user(uid, session)
			if user is None :
				UserTransactions().add_user_empty(uid)
			# Check if an entry already exists
			existing_entry = self.get(uid, gid)
			if existing_entry and new_record == False :
				return self.update(uid, gid, status=status, verification_date=verification_date, message_id=message_id, )

			# Create a new entry if one doesn't exist
			# noinspection PyTypeChecker
			new_entry = JoinHistory(
				uid=uid,
				gid=gid,
				status=status,
				verification_date=verification_date,
				message_id=message_id,
				created_date=created_at
			)
			session.add(new_entry)
			self.commit(session)
			logging.info(f"Added new join history for user {uid} in guild {gid}.")
			return new_entry

	def update(self, uid: int, gid: int, status: 'JoinHistoryStatus' = None,
	           verification_date: datetime = None, message_id: int = None,) -> 'JoinHistory | None' :
		"""
		Updates an existing JoinHistory entry.

		Only fields with non-None values will be updated.

		Args:
				uid: The user's unique ID.
				gid: The guild's unique ID.
				status: The new join status.
				verification_date: The new verification date.
				message_id: The new message ID.

		Returns:
				The updated JoinHistory object or None if not found.
		"""
		with self.createsession() as session :
			entry = self.get(uid, gid)
			if not entry :
				logging.warning(f"Attempted to update non-existent join history for user {uid} in guild {gid}.")
				return None

			# Prepare a dictionary of updates
			data = {
				"status"            : status,
				"verification_date" : verification_date,
				"message_id"        : message_id
			}

			# Apply updates for non-None values
			updated_fields = {}
			for field, value in data.items() :
				if value is not None :
					setattr(entry, field, value)
					updated_fields[field] = value

			if updated_fields :
				session.merge(entry)
				self.commit(session)
				logging.info(f"Updated join history for user {uid} in guild {gid} with: {updated_fields}")
			else :
				logging.info(f"No fields to update for join history of user {uid} in guild {gid}.")

			return entry

	def permanentdelete(self, uid: int, gid: int) -> bool :
		"""
		Permanently deletes a JoinHistory entry.

		Args:
				uid: The user's unique ID.
				gid: The guild's unique ID.

		Returns:
				True if deletion was successful, False otherwise.
		"""
		with self.createsession() as session :
			entry = self.get(uid, gid)
			if entry :
				session.delete(entry)
				self.commit(session)
				logging.info(f"Deleted join history for user {uid} in guild {gid}.")
				return True
			logging.warning(f"Attempted to delete non-existent join history for user {uid} in guild {gid}.")
			return False

	def fetch_previous_verifications(self, uid: int):
		with self.createsession() as session :
			if not isinstance(uid, int) :
				return []
			result =  session.execute(text(
				"""select b.name from join_history a
LEFT OUTER JOIN servers b on a.gid = b.guild
    where a.uid = :uid
    and a.status = 'SUCCESS'
limit 5;
		"""
			), {"uid": uid}).mappings().all()

			if len(result) < 1 :
				return []
			return result
	# Statistic functions go here
	def join_leave_graph_data(self, gid: int = None, days: int = 30) :
		# Ensure days is a safe integer to prevent SQL injection or interval manipulation
		if not isinstance(days, int) or days <= 0 :
			days = 30  # Fallback to default safely

		# Build the dynamic SQL condition safely without f-string interpolation
		guild_clause = ""
		params = {"days" : days}

		if gid and isinstance(gid, int) :
			guild_clause = "AND gid = :gid"
			params["gid"] = gid

		with self.createsession() as session :
			# We safely construct the query. :days and :gid are proper bound parameters.
			# Postgres allows '1 day' * :days as a safe way to bind numeric intervals.
			query = text(f"""
	            SELECT
	                GREATEST(created_date, last_updated)::date AS date_created,
	                status,
	                COUNT(*) AS records
	            FROM
	                join_history
	            WHERE
	                (created_date >= NOW() - INTERVAL '1 day' * :days OR
	                 last_updated >= NOW() - INTERVAL '1 day' * :days)
	                {guild_clause}
	            GROUP BY
	                date_created,
	                status
	            ORDER BY
	                date_created;
	        """)

			return session.execute(query, params).mappings().all()

	def age_graph_data(self, gid: int) :
		guild_clause = ""
		params = {}

		if gid and isinstance(gid, int) :
			guild_clause = "AND a.gid = :gid"  # Explicitly using a.gid to prevent ambiguity
			params["gid"] = gid

		with self.createsession() as session :
			# Using pure SQL bind parameters and explicitly qualifying columns
			query = text(f"""
	            SELECT
	                a.uid,
	                b.date_of_birth
	            FROM
	                join_history a
	            INNER JOIN users b ON a.uid = b.uid
	            WHERE b.date_of_birth IS NOT NULL
	              {guild_clause}
	        """)

			return session.execute(query, params).mappings().all()

	def anonymize_data(self, uid: int = None) :
		with self.createsession() as session :
			result = session.execute(text("UPDATE join_history set uid = :id where created_date < now() - INTERVAL '90 DAYS' and uid <> :id"), {'id': uid})
			self.commit(session)
			return result