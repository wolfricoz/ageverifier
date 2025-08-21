import unittest

from databases.controllers.ConfigTransactions import ConfigTransactions
from databases.current import create_bot_database, drop_bot_database


class TestAgeRoleTransactions(unittest.TestCase) :
	role_id = 9876543210
	key = "TESTKEY"
	value = "TESTVALUE"
	config = ConfigTransactions()

	def setUp(self) :
		from databases.Generators.guildgenerator import guildgenerator
		create_bot_database()
		self.guild: int = guildgenerator().create().guild  # Generates a unique guild ID per test

	def tearDown(self) :
		drop_bot_database()

	def test_config_unique_add_and_get(self) :
		added = self.config.config_unique_add(self.guild, self.key, self.value)
		self.assertTrue(added)

		result = self.config.config_unique_get(self.guild, self.key)
		self.assertIsNotNone(result)
		self.assertEqual(result.key, self.key)
		self.assertEqual(result.value, self.value)

	def test_config_unique_add_no_overwrite(self) :
		self.config.config_unique_add(self.guild, self.key, self.value)
		added_again = self.config.config_unique_add(self.guild, self.key, "NEW", overwrite=False)
		self.assertFalse(added_again)

	def test_config_unique_add_with_overwrite(self) :
		self.config.config_unique_add(self.guild, self.key, self.value)
		updated = self.config.config_unique_add(self.guild, self.key, "NEWVAL", overwrite=True)
		self.assertTrue(updated)

		result = self.config.config_unique_get(self.guild, self.key)
		self.assertEqual(result.value, "NEWVAL")

	def test_toggle_welcome_add_new(self) :
		toggled = self.config.toggle(self.guild, self.key, "ENABLED")
		self.assertFalse(toggled)

		result = self.config.config_unique_get(self.guild, self.key)
		self.assertEqual(result.value, "ENABLED")

	def test_toggle_welcome_update_existing(self) :
		self.config.config_unique_add(self.guild, self.key, "DISABLED", overwrite=True)
		toggled = self.config.toggle(self.guild, self.key, "ENABLED")
		self.assertTrue(toggled)

		result = self.config.config_unique_get(self.guild, self.key)
		self.assertEqual(result.value, "ENABLED")

	def test_config_key_add_and_remove(self) :
		added = self.config.config_key_add(self.guild, self.key, self.value, overwrite=False)
		self.assertTrue(added)

		removed = self.config.config_key_remove(self.guild, self.key, self.value)
		self.assertIsNone(removed)

		exists = self.config.key_multiple_exists_check(self.guild, self.key, self.value)
		self.assertFalse(exists)

	def test_key_exists_check(self) :
		self.assertFalse(self.config.key_exists_check(self.guild, self.key))
		self.config.config_unique_add(self.guild, self.key, self.value)
		self.assertTrue(self.config.key_exists_check(self.guild, self.key))

	def test_toggle_add(self) :
		self.config.toggle_add(self.guild, self.key, "ENABLED")

		result = self.config.config_unique_get(self.guild, self.key)
		self.assertIsNotNone(result)
		self.assertEqual(result.value, "ENABLED")

	def test_server_config_get(self) :
		self.config.config_key_add(self.guild, "KEY1", "VAL1", overwrite=False)
		self.config.config_key_add(self.guild, "KEY2", "VAL2", overwrite=False)

		configs = self.config.server_config_get(self.guild)
		keys = {cfg.key for cfg in configs}
		expected_keys = {
			"KEY1", "KEY2",
			"UPDATEROLES", "COOLDOWN", "WELCOME",
			"LOBBYWELCOME", "AUTOKICK", "AUTOMATIC", "PINGOWNER"
		}

		self.assertSetEqual(keys, expected_keys)
