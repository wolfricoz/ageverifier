import json
import unittest
from unittest import mock

from classes.configsetup import ConfigSetup
from databases.transactions.ConfigData import ConfigData
from resources.data.config_variables import channelchoices, rolechoices

GUILD_ID = 78


class FakeChannel :
	def __init__(self, channel_id, name, missing=None) :
		self.id = channel_id
		self.name = name
		self.missing = missing or []


class FakeRole :
	def __init__(self, role_id, name, position) :
		self.id = role_id
		self.name = name
		self.position = position


class FakeAgeRole :
	def __init__(self, role_id) :
		self.role_id = role_id


class FakeMe :
	def __init__(self, top_role, manage_roles=True) :
		self.top_role = top_role
		self.guild_permissions = mock.Mock(manage_roles=manage_roles)


class FakeGuild :
	def __init__(self, channels=None, roles=None, manage_roles=True) :
		self.id = GUILD_ID
		self.name = "Audit guild"
		self.channels = {channel.id : channel for channel in channels or []}
		self.roles = {role.id : role for role in roles or []}
		self.me = FakeMe(FakeRole(1, "Ageverifier", 10), manage_roles)

	def get_channel(self, channel_id) :
		return self.channels.get(channel_id)

	def get_role(self, role_id) :
		return self.roles.get(role_id)


class PermissionAuditBase(unittest.IsolatedAsyncioTestCase) :

	def setUp(self) :
		self.config = ConfigData()
		self.config.conf[GUILD_ID] = {}
		self.age_roles = []
		patches = [
			mock.patch("classes.configsetup.check_missing_channel_permissions",
			           side_effect=lambda channel, perms : [p for p in perms if p in channel.missing]),
			mock.patch("classes.configsetup.AgeRoleTransactions.get_all_guild", side_effect=lambda _ : self.age_roles),
		]
		for patcher in patches :
			patcher.start()
			self.addCleanup(patcher.stop)

	def tearDown(self) :
		self.config.conf.pop(GUILD_ID, None)

	def set_all_channels(self) :
		channels = []
		for i, key in enumerate(channelchoices.keys(), start=100) :
			self.config.conf[GUILD_ID][key.upper()] = str(i)
			channels.append(FakeChannel(i, key))
		return channels

	def set_all_roles(self) :
		roles = []
		for i, key in enumerate(rolechoices.keys(), start=200) :
			self.config.conf[GUILD_ID][key.upper()] = [i]
			roles.append(FakeRole(i, key, 1))
		return roles


class TestChannelAudit(PermissionAuditBase) :

	def test_every_channel_is_reported(self) :
		audit = ConfigSetup().audit_channel_permissions(FakeGuild())
		self.assertEqual([check["key"] for check in audit["checks"]], list(channelchoices.keys()))
		self.assertFalse(audit["ok"])

	def test_unset_channel(self) :
		check = ConfigSetup().audit_channel_permissions(FakeGuild())["checks"][0]
		self.assertEqual(check["status"], "not_set")
		self.assertIsNone(check["channel_id"])
		self.assertIn("/config channels", check["message"])

	def test_missing_permissions_use_notice_wording(self) :
		channels = self.set_all_channels()
		channels[0].missing = ["send_messages", "attach_files"]
		check = ConfigSetup().audit_channel_permissions(FakeGuild(channels))["checks"][0]
		self.assertEqual(check["status"], "missing")
		self.assertEqual([perm["label"] for perm in check["missing"]], ["Send Messages", "Attach Files"])
		self.assertEqual(check["missing"][0]["reason"], "post messages in the channel")
		self.assertEqual(check["message"], f"#{channels[0].name} is missing: Send Messages, Attach Files")

	def test_ids_are_strings(self) :
		# Discord ids overflow a JavaScript number, so the dashboard needs them as strings.
		channels = self.set_all_channels()
		check = ConfigSetup().audit_channel_permissions(FakeGuild(channels))["checks"][0]
		self.assertEqual(check["channel_id"], "100")

	def test_all_good(self) :
		audit = ConfigSetup().audit_channel_permissions(FakeGuild(self.set_all_channels()))
		self.assertTrue(audit["ok"])
		self.assertTrue(all(check["status"] == "ok" for check in audit["checks"]))


class TestRoleAudit(PermissionAuditBase) :

	def test_unset_key(self) :
		audit = ConfigSetup().audit_role_permissions(FakeGuild())
		self.assertEqual(audit["checks"][0]["status"], "not_set")
		self.assertEqual(audit["checks"][0]["message"], "This key was not set")
		self.assertFalse(audit["ok"])

	def test_role_above_bot_is_named(self) :
		roles = self.set_all_roles()
		roles[0].position = 10
		check = ConfigSetup().audit_role_permissions(FakeGuild(roles=roles))["checks"][0]
		self.assertEqual(check["status"], "above_bot")
		self.assertEqual(check["message"], f"I don't have permission to assign roles: {roles[0].name}")

	def test_single_role_key_stored_as_string(self) :
		roles = self.set_all_roles()
		self.config.conf[GUILD_ID]["APPROVAL_PING_ROLE"] = str(roles[-1].id)
		checks = ConfigSetup().audit_role_permissions(FakeGuild(roles=roles))["checks"]
		ping = next(check for check in checks if check["key"] == "approval_ping_role")
		self.assertEqual(ping["status"], "ok")

	def test_deleted_role(self) :
		roles = self.set_all_roles()
		self.config.conf[GUILD_ID]["VERIFICATION_ADD_ROLE"] = [roles[0].id, 999]
		check = ConfigSetup().audit_role_permissions(FakeGuild(roles=roles))["checks"][0]
		self.assertEqual(check["status"], "error")
		self.assertEqual(check["roles"][1], {"id" : "999", "name" : None, "status" : "not_found", "message" : "Unable to retrieve role"})

	def test_age_roles_are_checked(self) :
		roles = self.set_all_roles()
		roles.append(FakeRole(300, "18+", 20))
		self.age_roles = [FakeAgeRole(300)]
		check = ConfigSetup().audit_role_permissions(FakeGuild(roles=roles))["checks"][-1]
		self.assertEqual((check["key"], check["type"], check["status"]), ("age role", "age role", "above_bot"))

	def test_manage_roles(self) :
		audit = ConfigSetup().audit_role_permissions(FakeGuild(roles=self.set_all_roles(), manage_roles=False))
		self.assertFalse(audit["manage_roles"]["granted"])
		self.assertEqual(audit["manage_roles"]["label"], "Manage Roles")
		self.assertFalse(audit["ok"])


class TestFullAudit(PermissionAuditBase) :

	def test_counts_issues_and_serialises(self) :
		channels = self.set_all_channels()
		channels[0].missing = ["embed_links"]
		audit = ConfigSetup().audit_permissions(FakeGuild(channels, self.set_all_roles(), manage_roles=False))
		self.assertEqual(audit["issue_count"], 2)
		self.assertFalse(audit["ok"])
		self.assertEqual(audit["guild"], {"id" : str(GUILD_ID), "name" : "Audit guild"})
		json.dumps(audit)

	def test_clean_server(self) :
		audit = ConfigSetup().audit_permissions(FakeGuild(self.set_all_channels(), self.set_all_roles()))
		self.assertEqual(audit["issue_count"], 0)
		self.assertTrue(audit["ok"])


class TestEmbedsStillMatch(PermissionAuditBase) :
	"""The Discord embeds are rendered from the audit, so they must say what the dashboard says."""

	async def test_channel_embed(self) :
		channels = self.set_all_channels()
		channels[0].missing = ["send_messages"]
		embed = await ConfigSetup().create_permission_channels_embed(FakeGuild(channels))
		self.assertEqual(embed.fields[0].value, "❌ <#100> is missing: Send Messages")
		self.assertEqual(embed.fields[1].value, "✅ All required permissions are set")
		self.assertEqual(embed.fields[-1].name, "How to fix")
		self.assertEqual(embed.color.value, 0xff0000)

	async def test_role_embed(self) :
		roles = self.set_all_roles()
		self.config.conf[GUILD_ID]["VERIFICATION_ADD_ROLE"] = [999]
		embed = await ConfigSetup().create_permission_roles_embed(FakeGuild(roles=roles))
		self.assertEqual(embed.fields[0].value, "✅ I have permission to give roles")
		self.assertEqual((embed.fields[1].name, embed.fields[1].value), ("**verification_add_role - 999**", "❌ Unable to retrieve role"))
		self.assertEqual(embed.fields[2].value, "✅ I have permission to assign this role")
		self.assertEqual(embed.fields[-1].name, "How to fix")

	async def test_clean_embeds_have_no_fix_steps(self) :
		guild = FakeGuild(self.set_all_channels(), self.set_all_roles())
		for embed in (await ConfigSetup().create_permission_channels_embed(guild),
		              await ConfigSetup().create_permission_roles_embed(guild)) :
			self.assertNotIn("How to fix", [field.name for field in embed.fields])
			self.assertEqual(embed.color.value, 0x00ff00)
