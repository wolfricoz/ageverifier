import logging

import pymysql.err
from sqlalchemy import text
from sqlalchemy.exc import PendingRollbackError, InvalidRequestError, SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from databases.exceptions.CommitError import CommitError
from classes.singleton import singleton
from databases.current import engine


class DatabaseTransactions(metaclass=singleton) :
	sessionmanager = sessionmaker(bind=engine)

	def createsession(self) :
		return self.sessionmanager()

	def commit(self, session) :
		try :
			session.commit()
		except pymysql.err.InternalError as e :
			logging.warning(e)
			session.rollback()
			raise CommitError()
		except SQLAlchemyError as e :
			logging.warning(e)
			session.rollback()
			raise CommitError()
		finally :
			session.close()

	def ping_db(self) :
		try :
			with self.createsession() as session :
				session.execute(text("SELECT 1"))
				return "alive"
		except PendingRollbackError :
			logging.warning("Pending rollback during DB ping.")
			return "error"
		except InvalidRequestError :
			logging.warning("Invalid session state during DB ping.")
			return "alive"
		except SQLAlchemyError as e :
			logging.error(f"SQLAlchemy error during DB ping: {e}", exc_info=True)
			return "error"
		except Exception as e :
			logging.error(f"Unexpected error during DB ping: {e}", exc_info=True)
			return "error"
