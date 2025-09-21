import logging
from typing import Optional
from uuid import uuid4

from sqlalchemy import Select

from databases.controllers.DatabaseTransactions import DatabaseTransactions
from databases.current import WebsiteData


class WebsiteDataTransactions(DatabaseTransactions):
    """
    Handles database transactions for the LobbyData model.
    """

    def create(self, user_id: int, guild_id: int ) -> str:
        """
        Creates a new WebsiteData record.

        Returns:
            The newly created LobbyData object.
        """
        with self.createsession() as session:
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

    def read(self, uuid: str) -> Optional[WebsiteData]:
        """
        Retrieves a single WebsiteData entry by its message ID.

        Args:
            uuid: The ID of the Discord message.

        Returns:
            A LobbyData object or None if not found.
        """
        with self.createsession() as session:
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
