from sqlalchemy import Select

from databases.transactions.DatabaseTransactions import DatabaseTransactions
from databases.current import Timers


class TimersTransactions(DatabaseTransactions) :
	
	def add_timer(self, guildid, user_id, time_in_hours, role_id=None, reason=None) :
		"""Adds timer to the database"""
		with self.createsession() as session :
			entry = Timers(uid=user_id, guild=guildid, removal=time_in_hours, role=role_id, reason=reason)
			session.add(entry)
			self.commit(session)

	
	def get_timer_with_role(self, user_id: int, guild_id: int, role_id: int) :
		"""Gets the timer from the database with userid, guild and roleid"""
		with self.createsession() as session :

			timer = session.scalar(Select(Timers).where(Timers.uid == user_id, Timers.guild == guild_id, Timers.role == role_id))
			session.close()
			return timer

	
	def remove_timer(self, timer_id: int) :
		with self.createsession() as session :
			timer = session.scalar(Select(Timers).where(Timers.id == timer_id))
			session.delete(timer)
			self.commit(session)
