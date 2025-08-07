import unittest

from databases.Generators.guildgenerator import guildgenerator
from databases.Generators.uidgenerator import uidgenerator
from databases.controllers.TimersTransactions import TimersTransactions
from databases.controllers.UserTransactions import UserTransactions
from databases.current import create_bot_database, drop_bot_database


class TestTimersTransactions(unittest.TestCase):

    def setUp(self):
        create_bot_database()
        self.tt = TimersTransactions()
        self.guild = guildgenerator().create().guild
        self.user_id = uidgenerator().create()
        self.role_id = 1234567890

    def tearDown(self):
        drop_bot_database()

    def test_add_and_get_timer_with_role(self):

        user = UserTransactions().add_user_empty(self.user_id)
        self.tt.add_timer(self.guild, self.user_id, 5, role_id=self.role_id, reason="Test reason")
        timer = self.tt.get_timer_with_role(self.user_id, self.guild, self.role_id)
        self.assertIsNotNone(timer)
        self.assertEqual(timer.uid, self.user_id)
        self.assertEqual(timer.guild, self.guild)
        self.assertEqual(timer.role, self.role_id)
        self.assertEqual(timer.removal, 5)
        self.assertEqual(timer.reason, "Test reason")

    def test_get_timer_with_role_returns_none_if_missing(self):
        user = UserTransactions().add_user_empty(self.user_id)
        timer = self.tt.get_timer_with_role(self.user_id, 8888, 7777)
        self.assertIsNone(timer)

    def test_remove_timer(self):
        user = UserTransactions().add_user_empty(self.user_id)

        self.tt.add_timer(self.guild, self.user_id, 5, role_id=self.role_id)
        timer = self.tt.get_timer_with_role(self.user_id, self.guild, self.role_id)
        self.assertIsNotNone(timer)
        self.tt.remove_timer(timer.id)
        timer_after = self.tt.get_timer_with_role(self.user_id, self.guild, self.role_id)
        self.assertIsNone(timer_after)
