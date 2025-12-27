import datetime
import unittest

from classes.access import AccessControl
from databases.transactions.ServerTransactions import ServerTransactions
from databases.current import create_bot_database, drop_bot_database
from databases.Generators.guildgenerator import guildgenerator


class TestServerTransactions(unittest.TestCase):

    def setUp(self):
        create_bot_database()
        self.guild = guildgenerator().create().guild
        self.st = ServerTransactions()

    def tearDown(self):
        drop_bot_database()

    def test_add_new_guild_creates_entry(self):
        result = self.st.add(self.guild)
        self.assertEqual(result.guild, self.guild)

        # Check that configs were added for the guild by checking get_all configs
        # You might want to test that ConfigTransactions has added keys but for simplicity:
        # Just test the guild exists and is active
        guild_obj = self.st.get(self.guild)
        self.assertIsNotNone(guild_obj)
        self.assertTrue(guild_obj.active)

    def test_add_existing_guild_updates_and_returns(self):
        self.st.add(self.guild)  # Add first time
        # Add second time - should update and not duplicate
        result = self.st.add(self.guild)
        self.assertEqual(result.guild, self.guild)

        # Confirm only one entry exists
        all_guilds = self.st.get_all(id_only=False)
        matching = [g for g in all_guilds if g.guild == self.guild]
        self.assertEqual(len(matching), 1)

    def test_get_all_returns_ids_or_full_objects(self):
        guild2 = guildgenerator().create().guild
        self.st.add(self.guild)
        self.st.add(guild2)

        ids = self.st.get_all()
        self.assertIn(self.guild, ids)
        self.assertIn(guild2, ids)
        self.assertTrue(all(isinstance(gid, int) for gid in ids))

        full_objs = self.st.get_all(id_only=False)
        self.assertTrue(all(hasattr(g, 'guild') for g in full_objs))

    def test_get_returns_correct_guild_or_none(self):
        self.st.add(self.guild)
        found = self.st.get(self.guild)
        self.assertIsNotNone(found)
        self.assertEqual(found.guild, self.guild)

        missing = self.st.get(9999999999)
        self.assertIsNone(missing)

    def test_update_changes_active_status(self):
        self.st.add(self.guild)
        # Update active to False
        result = self.st.update(self.guild, active=False)
        self.assertTrue(result)

        updated = self.st.get(self.guild)
        self.assertFalse(updated.active)

    def test_update_nonexistent_returns_false(self):
        result = self.st.update(9999999999, active=True)
        self.assertFalse(result)

    def test_is_premium(self):
        AccessControl().reload()
        result = AccessControl().is_premium(self.guild)
        self.assertFalse(result)
        ServerTransactions().update(self.guild, premium=datetime.datetime.strptime("2030-01-01", "%Y-%m-%d"))
        AccessControl().reload()
        result = AccessControl().is_premium(self.guild)
        self.assertTrue(result)