import asyncio
import unittest
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import discord

from classes.lobby import Quarantine
from resources.data.config_variables import DEFAULT_QUARANTINE_HOURS, MAX_QUARANTINE_HOURS

GUILD_ID = 123
ROLE_ID = 456


def member(joined_hours_ago: float | None) :
	joined_at = None if joined_hours_ago is None else datetime.now(UTC) - timedelta(hours=joined_hours_ago)
	return MagicMock(joined_at=joined_at, add_roles=AsyncMock(), remove_roles=AsyncMock())


def config(values: dict) :
	data = MagicMock()
	data.get_key_or_none.side_effect = lambda guild_id, key : values.get(key)
	data.get_channel_id.side_effect = lambda guild_id, key : values.get(key)
	return patch.object(Quarantine, "ConfigData", return_value=data)


class TestQuarantineHours(unittest.TestCase) :
	def hours(self, value) :
		with config({"QUARANTINE_HOURS" : value}) :
			return Quarantine.quarantine_hours(GUILD_ID)

	def test_reads_the_stored_string(self) :
		self.assertEqual(self.hours("6"), 6)

	def test_defaults_when_unset_or_invalid(self) :
		self.assertEqual(self.hours(None), DEFAULT_QUARANTINE_HOURS)
		self.assertEqual(self.hours("None"), DEFAULT_QUARANTINE_HOURS)

	def test_clamps_to_the_allowed_range(self) :
		self.assertEqual(self.hours("0"), 1)
		self.assertEqual(self.hours("99999"), MAX_QUARANTINE_HOURS)


class TestApplyQuarantine(unittest.TestCase) :
	def apply(self, role, add_error=None) :
		target = member(0)
		target.guild.get_role.return_value = role
		target.add_roles.side_effect = add_error
		notify = AsyncMock()
		with config({"QUARANTINE_ROLE" : ROLE_ID if role else None}), \
				patch.object(Quarantine.PermissionNotice, "notify", notify) :
			result = asyncio.run(Quarantine.apply_quarantine(target))
		return result, target, notify

	def test_gives_the_role(self) :
		role = MagicMock()
		result, target, notify = self.apply(role)

		self.assertTrue(result)
		target.add_roles.assert_awaited_once()
		self.assertIs(target.add_roles.await_args.args[0], role)

	def test_false_without_a_role(self) :
		result, target, notify = self.apply(None)

		self.assertFalse(result)
		target.add_roles.assert_not_awaited()

	def test_tells_staff_when_the_bot_cannot_give_the_role(self) :
		result, target, notify = self.apply(MagicMock(), discord.Forbidden(MagicMock(status=403), "Missing Permissions"))

		self.assertFalse(result)
		notify.assert_awaited_once()
		self.assertEqual(notify.await_args.kwargs["missing"], ["manage_roles"])


class TestReleaseExpired(unittest.TestCase) :
	def release(self, members, hours="24", remove_error=None) :
		for m in members :
			m.remove_roles.side_effect = remove_error
		role = MagicMock(members=members)
		guild = MagicMock(id=GUILD_ID)
		guild.get_role.return_value = role
		bot = MagicMock(guilds=[guild])
		notify = AsyncMock()
		with config({"QUARANTINE_ROLE" : ROLE_ID, "QUARANTINE_HOURS" : hours}), \
				patch.object(Quarantine.PermissionNotice, "notify", notify) :
			released = asyncio.run(Quarantine.release_expired(bot))
		return released, notify

	def test_releases_only_members_whose_time_is_up(self) :
		served, waiting, unknown = member(25), member(2), member(None)
		released, _ = self.release([served, waiting, unknown])

		self.assertEqual(released, 2)
		served.remove_roles.assert_awaited_once()
		unknown.remove_roles.assert_awaited_once()
		waiting.remove_roles.assert_not_awaited()

	def test_uses_the_configured_duration(self) :
		target = member(2)
		released, _ = self.release([target], hours="1")

		self.assertEqual(released, 1)

	def test_stops_and_tells_staff_when_the_bot_cannot_remove_the_role(self) :
		first, second = member(30), member(30)
		released, notify = self.release([first, second],
		                                remove_error=discord.Forbidden(MagicMock(status=403), "Missing Permissions"))

		self.assertEqual(released, 0)
		notify.assert_awaited_once()
		second.remove_roles.assert_not_awaited()

	def test_skips_servers_without_a_role(self) :
		guild = MagicMock(id=GUILD_ID)
		with config({}) :
			released = asyncio.run(Quarantine.release_expired(MagicMock(guilds=[guild])))

		self.assertEqual(released, 0)


if __name__ == '__main__' :
	unittest.main()
