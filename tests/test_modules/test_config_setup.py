import unittest
from unittest import mock

import discord

from classes.configsetup import ConfigSetup
from databases.transactions.ConfigData import ConfigData
from resources.data.config_variables import VERIFICATION_KEY, VerificationMethods

GUILD_ID = 79


class FakeView :
	"""Stands in for a setup view: the 'button' is already pressed when setup waits on it."""

	def __init__(self, value) :
		self.value = value

	async def wait(self) :
		return None


class SetupVerificationBase(unittest.IsolatedAsyncioTestCase) :

	def setUp(self) :
		self.config = ConfigData()
		self.config.conf[GUILD_ID] = {VERIFICATION_KEY : str(VerificationMethods.IDVERIFY)}
		self.stored = {}
		patches = [
			mock.patch("classes.configsetup.ConfigTransactions.config_unique_add",
			           side_effect=lambda guild_id, key, value, overwrite=False : self.stored.update({key : value})),
			mock.patch("classes.configsetup.Queue"),
			mock.patch("classes.configsetup.ConfigUtils"),
			mock.patch("classes.configsetup.send_response", new_callable=mock.AsyncMock),
			# Only handed to the mocked Queue, never awaited.
			mock.patch("classes.configsetup.send_message", new_callable=mock.MagicMock),
		]
		for patcher in patches :
			patcher.start()
			self.addCleanup(patcher.stop)
		self.interaction = mock.MagicMock()
		self.interaction.guild.id = GUILD_ID
		self.interaction.channel.send = mock.AsyncMock()

	def tearDown(self) :
		self.config.conf.pop(GUILD_ID, None)

	def pick(self, value) :
		patcher = mock.patch("classes.configsetup.ConfigSelectVerificationMode", return_value=FakeView(value))
		patcher.start()
		self.addCleanup(patcher.stop)


class TestManualVerificationStep(SetupVerificationBase) :

	async def test_website(self) :
		self.pick(VerificationMethods.WEBSITE)
		setup = ConfigSetup()
		self.assertTrue(await setup.choose_verification_method(self.interaction))
		self.assertEqual(self.stored[VERIFICATION_KEY], VerificationMethods.WEBSITE)
		self.assertEqual(setup.changes[VERIFICATION_KEY], "WEBSITE")

	async def test_basic(self) :
		self.pick(VerificationMethods.BASIC)
		self.assertTrue(await ConfigSetup().choose_verification_method(self.interaction))
		self.assertEqual(self.stored[VERIFICATION_KEY], VerificationMethods.BASIC)

	async def test_skip_keeps_current_method(self) :
		self.pick("next")
		self.assertTrue(await ConfigSetup().choose_verification_method(self.interaction))
		self.assertNotIn(VERIFICATION_KEY, self.stored)

	async def test_cancel(self) :
		self.pick(None)
		self.assertFalse(await ConfigSetup().choose_verification_method(self.interaction))
		self.assertNotIn(VERIFICATION_KEY, self.stored)

	async def test_prompt_names_current_method(self) :
		self.pick("next")
		await ConfigSetup().choose_verification_method(self.interaction)
		self.assertIn("Currently set to **ID verification**", self.interaction.channel.send.call_args.args[0])

	async def test_cancel_stops_manual_setup(self) :
		self.pick(None)
		with mock.patch("classes.configsetup.ConfigSelectChannels") as channels :
			self.interaction.response.defer = mock.AsyncMock()
			self.assertFalse(await ConfigSetup().manual(mock.MagicMock(), self.interaction, {"age_log" : ""}, {}, {}))
		channels.assert_not_called()


class TestAutoVerificationMethod(SetupVerificationBase) :

	def stub_steps(self, setup) :
		setup.create_channels = mock.AsyncMock(return_value=True)
		setup.create_roles = mock.AsyncMock(return_value=True)
		setup.set_messages = mock.AsyncMock()
		setup.post_verify_button = mock.AsyncMock(return_value=None)

	async def test_auto_overrides_existing_method_with_website(self) :
		confirmation = mock.MagicMock(confirmed=True, send_message=mock.AsyncMock(), wait=mock.AsyncMock())
		setup = ConfigSetup()
		self.stub_steps(setup)
		with mock.patch("classes.configsetup.confirmAction", return_value=confirmation), \
				mock.patch("classes.configsetup.get", return_value=mock.MagicMock()) :
			self.assertTrue(await setup.auto(self.interaction, {}, {}, {}))
		self.assertEqual(self.stored[VERIFICATION_KEY], VerificationMethods.WEBSITE)

	async def test_auto_cancelled_leaves_method_alone(self) :
		confirmation = mock.MagicMock(confirmed=False, send_message=mock.AsyncMock(), wait=mock.AsyncMock())
		with mock.patch("classes.configsetup.confirmAction", return_value=confirmation) :
			self.assertFalse(await ConfigSetup().auto(self.interaction, {}, {}, {}))
		self.assertNotIn(VERIFICATION_KEY, self.stored)

	async def test_dashboard_auto_setup_uses_website(self) :
		setup = ConfigSetup()
		self.stub_steps(setup)
		guild = mock.MagicMock(id=GUILD_ID)
		self.config.conf[GUILD_ID]["APPROVAL_CHANNEL"] = "300"
		with mock.patch("classes.configsetup.get", return_value=mock.MagicMock()) :
			await setup.api_auto_setup(guild)
		self.assertEqual(self.stored[VERIFICATION_KEY], VerificationMethods.WEBSITE)


	async def test_auto_does_not_prompt_for_optional_roles(self) :
		confirmation = mock.MagicMock(confirmed=True, send_message=mock.AsyncMock(), wait=mock.AsyncMock())
		setup = ConfigSetup()
		self.stub_steps(setup)
		with mock.patch("classes.configsetup.confirmAction", return_value=confirmation), \
				mock.patch("classes.configsetup.get", return_value=mock.MagicMock()) :
			await setup.auto(self.interaction, {}, {"server_join_role" : ""}, {})
		# Without an interaction create_roles only makes the Verified role.
		self.assertEqual(len(setup.create_roles.await_args.args), 2)
		setup.post_verify_button.assert_awaited_once()


class TestSetupPrompts(SetupVerificationBase) :

	async def prompt(self, value, stored=None) :
		if stored is not None :
			self.config.conf[GUILD_ID]["VERIFICATION_REMOVE_ROLE"] = stored
		view = FakeView(value)
		with mock.patch("classes.configsetup.ConfigSelectRoles", return_value=view) as roles, \
				mock.patch("classes.configsetup.ConfigTransactions.config_unique_remove") as remove :
			setup = ConfigSetup()
			result = await setup.prompt_choice(self.interaction, "verification_remove_role", "description", "role")
		return result, setup, roles, remove

	async def test_shows_the_current_value_and_offers_clear(self) :
		result, setup, roles, remove = await self.prompt("next", stored="555")
		text = self.interaction.channel.send.call_args.args[0]
		self.assertIn("**Roles removed after verification** (optional)", text)
		self.assertIn("Current: <@&555>. **Skip** keeps it, **Clear** removes it.", text)
		roles.assert_called_once_with(True)
		self.assertTrue(result)
		self.assertEqual(self.stored, {})

	async def test_unset_value_has_no_clear(self) :
		await self.prompt("next")
		self.assertIn("Not set yet.", self.interaction.channel.send.call_args.args[0])

	async def test_clear_removes_the_value(self) :
		result, setup, roles, remove = await self.prompt("clear", stored="555")
		remove.assert_called_once_with(GUILD_ID, "verification_remove_role")
		self.assertIsNone(setup.changes["verification_remove_role"])

	async def test_the_prompt_never_pings_the_role(self) :
		await self.prompt("next", stored="555")
		self.assertIn("allowed_mentions", self.interaction.channel.send.call_args.kwargs)


class TestDoneMessage(unittest.TestCase) :

	def test_names_the_button_and_report_channels(self) :
		setup = ConfigSetup()
		setup.verify_button_channel = mock.MagicMock(mention="#lobby")
		report = mock.MagicMock(spec=discord.TextChannel, mention="#lobby-moderation")
		with mock.patch.object(ConfigSetup, "permission_report_channel", return_value=report) :
			text = setup.done_message(mock.MagicMock(), "auto")
		self.assertIn("The verify button is posted in #lobby.", text)
		self.assertIn("The permission check is being posted in #lobby-moderation.", text)
		self.assertIn("/config roles", text)

	def test_without_a_button_it_says_how_to_post_one(self) :
		with mock.patch.object(ConfigSetup, "permission_report_channel", return_value=None) :
			text = ConfigSetup().done_message(mock.MagicMock(), "manual")
		self.assertIn("`/lobby button`", text)

