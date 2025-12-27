import logging

from sqlalchemy import Select, func

from databases import current as db
from databases.transactions.DatabaseTransactions import DatabaseTransactions
from databases.current import AgeRole


class AgeRoleTransactions(DatabaseTransactions) :

	def exists(self, role_id) :
		with self.createsession() as session :
			return session.scalar(Select(AgeRole).where(AgeRole.role_id == role_id))

	def get(self, guild_id, role_id) :
		with self.createsession() as session :
			return session.scalar(Select(AgeRole).where(AgeRole.guild_id == guild_id, AgeRole.role_id == role_id))

	def get_all(self, guild_id) :
		with self.createsession() as session :
			return session.scalars(Select(AgeRole).where(AgeRole.guild_id == guild_id)).all()

	def get_minimum_age(self, guild_id) :
		with self.createsession() as session :
			return session.scalars(Select(func.min(AgeRole.minimum_age)).where(AgeRole.guild_id == guild_id)).first()

	def add(self, guild_id, role_id, role_type, maximum_age=200, minimum_age=18, reload=True) :
		with self.createsession() as session :
			if self.exists(role_id) :
				return self.update(guild_id, role_id, role_type, maximum_age, minimum_age, reload=reload)
			role = db.AgeRole(guild_id=guild_id, role_id=role_id, type=role_type, maximum_age=maximum_age,
			                  minimum_age=minimum_age)
			session.merge(role)
			self.commit(session)
			if reload :
				self.reload_guild(guild_id)
			return role

	def permanentdelete(self, guild_id, role_id) :
		with self.createsession() as session :
			role = session.scalar(Select(AgeRole).where(AgeRole.role_id == role_id))
			session.delete(role)
			self.commit(session)

	def update(self, guild_id: int, role_id: int, role_type: str = None, maximum_age: int = None,
	           minimum_age: int = None, reload=True) :
		with self.createsession() as session :
			role = session.scalar(Select(AgeRole).where(AgeRole.role_id == role_id))
			data = {
				"type"        : role_type.upper(),
				"maximum_age" : maximum_age,
				"minimum_age" : minimum_age
			}
			for field, value in data.items() :
				if value is not None :
					setattr(role, field, value)
			session.merge(role)
			self.commit(session)
			logging.info(f"Updated {role_id} with:")
			logging.info(data)
			if reload :
				self.reload_guild(guild_id)

			return role
