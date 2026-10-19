import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import discord
from discord.ext.commands import GroupCog

import modules.Lobby as lobby_module
import modules.idcheck as idcheck_module
from listeners.LobbyListeners import LobbyListeners
from modules.Surveys import Surveys


def forbidden() :
	return discord.Forbidden(MagicMock(status=403), "Missing Permissions")


class TestListenerCogsHaveNoSlashGroup(unittest.TestCase) :
	"""As GroupCogs without commands they registered /lobby-listeners and /surveys, which failed when run."""

	def test_not_group_cogs(self) :
		self.assertFalse(issubclass(LobbyListeners, GroupCog))
		self.assertFalse(issubclass(Surveys, GroupCog))


class TestReturnLobby(unittest.TestCase) :

	def run_command(self, config, user_roles, remove_error=None) :
		roles = {1 : MagicMock(name="verified"), 2 : MagicMock(name="unverified")}
		interaction = MagicMock()
		interaction.response.defer = AsyncMock()
		interaction.followup.send = AsyncMock()
		interaction.guild.get_role.side_effect = lambda role_id : roles.get(role_id)
		user = MagicMock(roles=[roles[i] for i in user_roles], remove_roles=AsyncMock(side_effect=remove_error),
		                 add_roles=AsyncMock())
		data = MagicMock()
		data.get_key_or_none.side_effect = lambda guild_id, key : config.get(key)
		respond = AsyncMock()
		with patch.object(lobby_module, "ConfigData", return_value=data), \
				patch.object(lobby_module.PermissionNotice, "respond", respond) :
			asyncio.run(lobby_module.Lobby.returnlobby.callback(MagicMock(), interaction, user))
		return roles, user, interaction, respond

	def test_deleted_roles_are_skipped(self) :
		config = {"verification_add_role" : ["1", "999"], "verification_remove_role" : "2"}
		roles, user, interaction, respond = self.run_command(config, user_roles=[1])

		user.remove_roles.assert_awaited_once()
		self.assertEqual(list(user.remove_roles.await_args.args), [roles[1]])
		self.assertEqual(list(user.add_roles.await_args.args), [roles[2]])
		self.assertIn("moved back to the lobby", interaction.followup.send.await_args.args[0])

	def test_age_roles_are_removed(self) :
		"""The age roles are cached as {role_id: {"MAX": .., "MIN": ..}}; reading that as one value skipped every age role."""
		config = {"verification_add_role" : {1 : {"MAX" : 99, "MIN" : 18}, 999 : {"MAX" : 17, "MIN" : 13}}}
		roles, user, interaction, respond = self.run_command(config, user_roles=[1])

		self.assertEqual(list(user.remove_roles.await_args.args), [roles[1]])
		self.assertIn("moved back to the lobby", interaction.followup.send.await_args.args[0])

	def test_nothing_to_change_says_so(self) :
		roles, user, interaction, respond = self.run_command({}, user_roles=[])

		user.remove_roles.assert_not_awaited()
		self.assertIn("nothing to change", interaction.followup.send.await_args.args[0])

	def test_role_order_problem_gets_a_notice(self) :
		config = {"verification_add_role" : "1"}
		roles, user, interaction, respond = self.run_command(config, user_roles=[1], remove_error=forbidden())

		self.assertEqual(respond.await_args.kwargs["missing"], ["manage_roles"])


class TestIdcheckCommands(unittest.TestCase) :

	def transactions(self, entry) :
		transactions = MagicMock()
		transactions.get_id_info.return_value = entry
		return transactions

	def create(self, entry) :
		transactions = self.transactions(entry)
		confirm = MagicMock(return_value=MagicMock(send_confirm=AsyncMock(return_value=True)))
		with patch.object(idcheck_module, "VerificationTransactions", return_value=transactions), \
				patch.object(idcheck_module, "Confirm", confirm), \
				patch.object(idcheck_module, "send_response", AsyncMock()) :
			asyncio.run(idcheck_module.idcheck.create.callback(MagicMock(), MagicMock(), MagicMock(), "reason"))
		return transactions, confirm

	def test_create_after_delete_does_not_ask_to_update(self) :
		transactions, confirm = self.create(SimpleNamespace(idcheck=False, reason=None))

		confirm.assert_not_called()
		transactions.update_check.assert_called_once()

	def test_create_on_a_flagged_entry_asks_first(self) :
		transactions, confirm = self.create(SimpleNamespace(idcheck=True, reason="old"))

		self.assertIn("`old`", confirm.return_value.send_confirm.await_args.args[1])

	def test_send_after_delete_asks_for_a_reason(self) :
		transactions = self.transactions(SimpleNamespace(idcheck=False, reason=None))
		modal = AsyncMock(return_value=None)
		chooser = MagicMock()
		with patch.object(idcheck_module, "VerificationTransactions", return_value=transactions), \
				patch.object(idcheck_module.AccessControl, "is_premium", return_value=True), \
				patch.object(idcheck_module, "ReasonChoice", chooser), \
				patch.object(idcheck_module, "send_modal", modal) :
			asyncio.run(idcheck_module.idcheck.send.callback(MagicMock(), MagicMock(), MagicMock()))

		chooser.assert_not_called()
		modal.assert_awaited_once()


if __name__ == '__main__' :
	unittest.main()
