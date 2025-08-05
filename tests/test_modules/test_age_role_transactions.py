import unittest

from databases.current import create_bot_database, drop_bot_database
from databases.controllers.AgeRoleTransactions import AgeRoleTransactions


class TestAgeRoleTransactions(unittest.TestCase):
    role_id = 9876543210

    def setUp(self):
        from databases.Generators.guildgenerator import guildgenerator
        create_bot_database()
        self.guild = guildgenerator().create().guild  # Generates a unique guild ID per test

    def tearDown(self):
        drop_bot_database()

    def test_add_role(self):
        controller = AgeRoleTransactions()
        role = controller.add(self.guild, self.role_id, "ADULT", maximum_age=30, minimum_age=18)
        self.assertEqual(role.role_id, self.role_id)
        self.assertEqual(role.guild_id, self.guild)
        self.assertEqual(role.minimum_age, 18)
        self.assertEqual(role.maximum_age, 30)

    def test_exists(self):
        controller = AgeRoleTransactions()
        controller.add(self.guild, self.role_id, "ADULT")
        self.assertTrue(controller.exists(self.role_id))

    def test_get_role(self):
        controller = AgeRoleTransactions()
        controller.add(self.guild, self.role_id, "ADULT")
        role = controller.get(self.guild, self.role_id)
        self.assertIsNotNone(role)
        self.assertEqual(role.role_id, self.role_id)

    def test_get_all_roles(self):
        controller = AgeRoleTransactions()
        controller.add(self.guild, self.role_id, "ADULT")
        controller.add(self.guild, self.role_id + 1, "TEEN")
        roles = controller.get_all(self.guild)
        self.assertEqual(len(roles), 2)

    def test_get_minimum_age(self):
        controller = AgeRoleTransactions()
        controller.add(self.guild, self.role_id, "ADULT", minimum_age=25)
        controller.add(self.guild, self.role_id + 1, "TEEN", minimum_age=16)
        controller.add(self.guild, self.role_id + 2, "SENIOR", minimum_age=60)
        min_age = controller.get_minimum_age(self.guild)
        self.assertEqual(min_age, 16)

    def test_update_role(self):
        controller = AgeRoleTransactions()
        controller.add(self.guild, self.role_id, "ADULT", maximum_age=30, minimum_age=18)
        updated = controller.update(self.guild, self.role_id, role_type="SENIOR", minimum_age=60, maximum_age=80)
        self.assertEqual(updated.type, "SENIOR")
        self.assertEqual(updated.minimum_age, 60)
        self.assertEqual(updated.maximum_age, 80)

    def test_permanent_delete(self):
        controller = AgeRoleTransactions()
        controller.add(self.guild, self.role_id, "ADULT")
        controller.permanentdelete(self.guild, self.role_id)
        self.assertIsNone(controller.get(self.guild, self.role_id))