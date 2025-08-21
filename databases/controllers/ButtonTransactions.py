import logging
from typing import Optional

from sqlalchemy import Select

from classes.encryption import Encryption
from databases.controllers.DatabaseTransactions import DatabaseTransactions
from databases.current import LobbyData


class LobbyDataTransactions(DatabaseTransactions):
    """
    Handles database transactions for the LobbyData model.
    """

    def create(self, uuid: str, user_id: int,  dob: str, age: int) -> LobbyData:
        """
        Creates a new LobbyData record.

        Args:
            uuid: The ID of the Discord message.
            dob: The verified date of birth.
            age: The age of the user.

        Returns:
            The newly created LobbyData object.
        """
        with self.createsession() as session:
            new_entry = LobbyData(
                uuid=uuid,
                uid=user_id,
                dob=Encryption().encrypt(dob),
                age=age
            )
            session.add(new_entry)
            self.commit(session)
            logging.info(f"Created new lobby data for message_id: {user_id}.")
            return new_entry

    def read(self, uuid: str) -> Optional[LobbyData]:
        """
        Retrieves a single LobbyData entry by its message ID.

        Args:
            uuid: The ID of the Discord message.

        Returns:
            A LobbyData object or None if not found.
        """
        with self.createsession() as session:
            return session.scalar(
                Select(LobbyData)
                .where(LobbyData.uuid == uuid)
            )

    def delete(self, uuid: str) -> bool:
        """
        Permanently deletes a LobbyData entry.

        Args:
            uuid: The ID of the Discord message.

        Returns:
            True if deletion was successful, False otherwise.
        """
        with self.createsession() as session:
            entry = self.read(uuid)
            if entry:
                session.delete(entry)
                self.commit(session)
                logging.info(f"Deleted lobby data for message_id: {uuid}.")
                return True
            logging.warning(f"Attempted to delete non-existent lobby data for message_id: {uuid}.")
            return False

