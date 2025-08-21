import unittest
from datetime import datetime, timezone

from databases.Generators.guildgenerator import guildgenerator
from databases.Generators.uidgenerator import uidgenerator
from databases.controllers.HistoryTransactions import JoinHistoryTransactions
from databases.current import create_bot_database, drop_bot_database
from databases.enums.joinhistorystatus import JoinHistoryStatus


# Assuming the following are defined elsewhere in your project
# from databases.current import create_bot_database, drop_bot_database
# from databases.controllers.JoinHistoryTransactions import JoinHistoryTransactions
# from databases.models import JoinHistoryStatus
# from databases.Generators.guildgenerator import guildgenerator
# from databases.Generators.usergenerator import usergenerator


class TestJoinHistoryTransactions(unittest.TestCase):
    """
    Test suite for the JoinHistoryTransactions controller.
    """

    def setUp(self):
        """
        Set up a clean database and generate unique user and guild IDs for each test.
        """
        # from databases.Generators.guildgenerator import guildgenerator
        # from databases.Generators.usergenerator import usergenerator
        create_bot_database()
        # Generates a unique guild and user ID per test
        self.guild_id = guildgenerator().create().guild
        self.user_id = uidgenerator().create()

    def tearDown(self):
        """
        Drop the database after each test to ensure isolation.
        """
        drop_bot_database()

    def test_add_entry(self):
        """
        Tests adding a new join history entry.
        """
        controller = JoinHistoryTransactions()
        entry = controller.add(self.user_id, self.guild_id, status=JoinHistoryStatus.VERIFIED)
        self.assertIsNotNone(entry)
        self.assertEqual(entry.uid, self.user_id)
        self.assertEqual(entry.gid, self.guild_id)
        self.assertEqual(entry.status, JoinHistoryStatus.VERIFIED)

    def test_add_or_update_existing_entry(self):
        """
        Tests that calling 'add' on an existing entry updates it instead of creating a new one.
        """
        controller = JoinHistoryTransactions()
        # First add
        controller.add(self.user_id, self.guild_id, status=JoinHistoryStatus.NEW)
        # Second add for the same user/guild should trigger an update
        updated_entry = controller.add(self.user_id, self.guild_id, status=JoinHistoryStatus.SUCCESS, new_record=False)

        self.assertEqual(updated_entry.status, JoinHistoryStatus.SUCCESS)
        # Verify there is still only one entry
        all_entries = controller.get_all_for_user(self.user_id)
        self.assertEqual(len(all_entries), 1)

    def test_get_entry(self):
        """
        Tests retrieving a specific join history entry.
        """
        controller = JoinHistoryTransactions()
        controller.add(self.user_id, self.guild_id, status=JoinHistoryStatus.NEW)
        entry = controller.get(self.user_id, self.guild_id)
        self.assertIsNotNone(entry)
        self.assertEqual(entry.uid, self.user_id)
        self.assertEqual(entry.gid, self.guild_id)

    def test_get_all_for_guild(self):
        """
        Tests retrieving all join history entries for a specific guild.
        """
        controller = JoinHistoryTransactions()
        # from databases.Generators.usergenerator import usergenerator
        user2_id = uidgenerator().create()
        user3_id = uidgenerator().create()

        controller.add(self.user_id, self.guild_id, status=JoinHistoryStatus.VERIFIED)
        controller.add(user2_id, self.guild_id, status=JoinHistoryStatus.NEW)
        # Add entry for a different guild to ensure it's not fetched
        guild = guildgenerator().create()
        controller.add(user3_id, guild.guild, status=JoinHistoryStatus.SUCCESS)

        guild_entries = controller.get_all_for_guild(self.guild_id)
        self.assertEqual(len(guild_entries), 2)

    def test_get_all_for_user(self):
        """
        Tests retrieving all join history entries for a specific user.
        """
        controller = JoinHistoryTransactions()
        # from databases.Generators.guildgenerator import guildgenerator
        guild2_id = guildgenerator().create().guild
        guild3_id = guildgenerator().create().guild

        controller.add(self.user_id, self.guild_id, status=JoinHistoryStatus.VERIFIED)
        controller.add(self.user_id, guild2_id, status=JoinHistoryStatus.NEW)
        # Add entry for a different user to ensure it's not fetched
        controller.add(self.user_id + 1, guild3_id, status=JoinHistoryStatus.SUCCESS)

        user_entries = controller.get_all_for_user(self.user_id)
        self.assertEqual(len(user_entries), 2)

    def test_update_entry(self):
        """
        Tests updating an existing join history entry.
        """
        controller = JoinHistoryTransactions()
        controller.add(self.user_id, self.guild_id, status=JoinHistoryStatus.NEW)

        verification_time = datetime.now(timezone.utc)
        message_id = 1234567890
        updated_entry = controller.update(
            self.user_id,
            self.guild_id,
            status=JoinHistoryStatus.VERIFIED,
            verification_date=verification_time,
            message_id=message_id
        )
        self.assertEqual(updated_entry.status, JoinHistoryStatus.VERIFIED)
        self.assertEqual(updated_entry.verification_date, verification_time)
        self.assertEqual(updated_entry.message_id, message_id)

    def test_permanent_delete(self):
        """
        Tests permanently deleting a join history entry.
        """
        controller = JoinHistoryTransactions()
        controller.add(self.user_id, self.guild_id, status=JoinHistoryStatus.VERIFIED)

        # Ensure it exists before delete
        self.assertIsNotNone(controller.get(self.user_id, self.guild_id))

        delete_successful = controller.permanentdelete(self.user_id, self.guild_id)
        self.assertTrue(delete_successful)

        # Ensure it is gone after delete
        self.assertIsNone(controller.get(self.user_id, self.guild_id))
