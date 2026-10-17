import asyncio
import unittest
from unittest.mock import patch

from databases import current as db
from databases.current import clear_bot_database, create_bot_database
from databases.exceptions.CommitError import CommitError
from databases.transactions.AgeRoleTransactions import AgeRoleTransactions
from databases.transactions.ConfigData import ConfigData
from databases.transactions.ConfigTransactions import ConfigTransactions


class TestLoadAllGuilds(unittest.TestCase) :
	"""load_all_guilds fills the cache with two queries; it has to give the same result as loading guilds one by one."""

	def setUp(self) :
		from databases.Generators.guildgenerator import guildgenerator
		create_bot_database()
		self.guild: int = guildgenerator().create().guild
		self.other_guild: int = guildgenerator().create().guild
		self.data = ConfigData()
		self.data.cleanup()

	def tearDown(self) :
		self.data.cleanup()
		clear_bot_database()

	def seed(self) :
		ConfigTransactions().config_unique_add(self.guild, "APPROVAL_CHANNEL", "300")
		ConfigTransactions().config_key_add(self.guild, "SERVER_JOIN_ROLE", "11", overwrite=False)
		ConfigTransactions().config_key_add(self.guild, "SERVER_JOIN_ROLE", "12", overwrite=False)
		AgeRoleTransactions().add(self.guild, 777, "ADULT", maximum_age=30, minimum_age=18, reload=False)

	def raw_config(self, key: str, value: str) :
		"""Stores a row without the reload the transaction helpers do, like data written before a migration."""
		transactions = ConfigTransactions()
		with transactions.createsession() as session :
			session.add(db.Config(guild=self.guild, key=key, value=value))
			transactions.commit(session)

	def load_all(self, guild_ids) :
		asyncio.run(self.data.load_all_guilds(guild_ids))

	def test_matches_loading_the_guild_on_its_own(self) :
		self.seed()
		self.data.load_guild(self.guild)
		single = self.data.conf[self.guild]
		self.data.cleanup()

		self.load_all([self.guild])

		self.assertEqual(self.data.conf[self.guild], single)
		# The old bulk loader reset list keys on every row, keeping only the last value.
		self.assertEqual(single["SERVER_JOIN_ROLE"], [11, 12])
		self.assertEqual(single["VERIFICATION_ADD_ROLE"], {777 : {"MAX" : 30, "MIN" : 18}})

	def test_loaded_guilds_are_not_loaded_again_on_lookup(self) :
		self.load_all([self.guild, self.other_guild])

		with patch.object(ConfigData, "load_guild") as load_guild :
			self.data.get_guild(self.guild)
			self.data.get_guild(self.other_guild)

		load_guild.assert_not_called()

	def test_drops_guilds_left_out(self) :
		self.data.conf[self.other_guild] = {}

		self.load_all([self.guild])

		self.assertNotIn(self.other_guild, self.data.conf)

	def test_reloads_a_guild_that_changed_during_the_load(self) :
		self.seed()
		build = ConfigData._build_guilds

		def build_then_change(data, guild_ids) :
			result = build(data, guild_ids)
			ConfigTransactions().config_unique_add(self.guild, "APPROVAL_CHANNEL", "400", overwrite=True)
			return result

		with patch.object(ConfigData, "_build_guilds", build_then_change) :
			self.load_all([self.guild])

		self.assertEqual(self.data.conf[self.guild]["APPROVAL_CHANNEL"], "400")

	def test_old_age_role_rows_go_through_load_guild(self) :
		self.raw_config("VERIFICATION_ADD_ROLE", "888")

		with patch.object(ConfigData, "load_guild") as load_guild :
			self.load_all([self.guild, self.other_guild])

		load_guild.assert_called_once_with(self.guild)

	def test_a_guild_that_fails_to_reload_keeps_its_bulk_config(self) :
		self.seed()
		self.raw_config("VERIFICATION_ADD_ROLE", "888")

		with patch.object(ConfigData, "load_guild", side_effect=CommitError()) :
			self.load_all([self.guild])

		self.assertEqual(self.data.conf[self.guild]["APPROVAL_CHANNEL"], "300")

	def test_skips_non_numeric_list_values(self) :
		self.raw_config("SERVER_JOIN_ROLE", "None")
		self.raw_config("SERVER_JOIN_ROLE", "13")

		self.load_all([self.guild])

		self.assertEqual(self.data.conf[self.guild]["SERVER_JOIN_ROLE"], [13])


if __name__ == '__main__' :
	unittest.main()
