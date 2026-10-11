import unittest
from unittest import mock

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
