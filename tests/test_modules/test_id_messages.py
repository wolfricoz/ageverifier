import asyncio
import re
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import discord

from classes.verification import idmessages
from views.buttons import idwithdrawbutton
from views.buttons.idwithdrawbutton import IdWithdrawButton

CHANNEL_ID = 111
STAFF_MESSAGE_ID = 222


def dm_message(with_button: bool = True) :
	components = [SimpleNamespace(children=[SimpleNamespace(
		custom_id=idmessages.withdraw_custom_id(CHANNEL_ID, STAFF_MESSAGE_ID))])] if with_button else []
	return MagicMock(components=components, delete=AsyncMock())


def not_found() :
	return discord.NotFound(MagicMock(status=404), "Unknown Message")


class TestStaffReviewReference(unittest.TestCase) :
	def test_reads_the_staff_message_from_the_withdraw_button(self) :
		self.assertEqual(idmessages.staff_review_reference(dm_message()), (CHANNEL_ID, STAFF_MESSAGE_ID))

	def test_none_for_messages_without_the_button(self) :
		self.assertIsNone(idmessages.staff_review_reference(dm_message(with_button=False)))

	def test_button_custom_id_matches_its_template(self) :
		button = IdWithdrawButton(CHANNEL_ID, STAFF_MESSAGE_ID)
		match = re.fullmatch(idmessages.WITHDRAW_ID_TEMPLATE, button.item.custom_id)
		self.assertEqual((int(match["channel_id"]), int(match["message_id"])), (CHANNEL_ID, STAFF_MESSAGE_ID))


class TestExpireIdMessages(unittest.TestCase) :
	"""expire_id_messages with the database and Discord mocked out."""

	def run_expiry(self, message=None, fetch_error=None) :
		transactions = MagicMock()
		transactions.get_expired_idmessages.return_value = [SimpleNamespace(uid=10, idmessage=99)]
		dm_channel = MagicMock(fetch_message=AsyncMock(return_value=message, side_effect=fetch_error))
		bot = MagicMock()
		bot.get_user.return_value = MagicMock(dm_channel=dm_channel)
		close = AsyncMock()
		with patch.object(idmessages, "VerificationTransactions", return_value=transactions), \
				patch.object(idmessages, "close_staff_review", close) :
			cleared = asyncio.run(idmessages.expire_id_messages(bot))
		return cleared, transactions, close

	def test_deletes_the_image_clears_the_record_and_closes_the_review(self) :
		message = dm_message()
		cleared, transactions, close = self.run_expiry(message)

		self.assertEqual(cleared, 1)
		message.delete.assert_awaited_once()
		transactions.remove_idmessage.assert_called_once_with(10)
		close.assert_awaited_once()
		self.assertEqual(close.await_args.args[1 :3], (CHANNEL_ID, STAFF_MESSAGE_ID))

	def test_clears_the_record_when_the_message_is_already_gone(self) :
		cleared, transactions, close = self.run_expiry(fetch_error=not_found())

		self.assertEqual(cleared, 1)
		transactions.remove_idmessage.assert_called_once_with(10)
		close.assert_not_awaited()

	def test_keeps_the_record_for_a_retry_on_other_discord_errors(self) :
		error = discord.HTTPException(MagicMock(status=500), "Server Error")
		cleared, transactions, close = self.run_expiry(fetch_error=error)

		self.assertEqual(cleared, 0)
		transactions.remove_idmessage.assert_not_called()
		close.assert_not_awaited()


class TestWithdrawButton(unittest.TestCase) :
	def run_withdraw(self, current_message_id=5, delete_error=None) :
		interaction = MagicMock()
		interaction.response.defer = AsyncMock()
		interaction.message = MagicMock(id=5, delete=AsyncMock(side_effect=delete_error))
		interaction.user = MagicMock(id=10, mention="<@10>")
		transactions = MagicMock()
		transactions.get_id_info.return_value = SimpleNamespace(idmessage=current_message_id)
		close = AsyncMock()
		with patch.object(idwithdrawbutton, "VerificationTransactions", return_value=transactions), \
				patch.object(idwithdrawbutton, "close_staff_review", close), \
				patch.object(idwithdrawbutton, "send_response", AsyncMock()) :
			asyncio.run(IdWithdrawButton(CHANNEL_ID, STAFF_MESSAGE_ID).callback(interaction))
		return interaction, transactions, close

	def test_deletes_the_id_and_closes_the_review(self) :
		interaction, transactions, close = self.run_withdraw()

		interaction.message.delete.assert_awaited_once()
		transactions.remove_idmessage.assert_called_once_with(10)
		self.assertEqual(close.await_args.args[1 :3], (CHANNEL_ID, STAFF_MESSAGE_ID))

	def test_leaves_a_newer_submission_alone(self) :
		_, transactions, close = self.run_withdraw(current_message_id=6)

		transactions.remove_idmessage.assert_not_called()
		close.assert_awaited_once()

	def test_does_nothing_else_when_the_delete_fails(self) :
		error = discord.HTTPException(MagicMock(status=500), "Server Error")
		_, transactions, close = self.run_withdraw(delete_error=error)

		transactions.remove_idmessage.assert_not_called()
		close.assert_not_awaited()


if __name__ == '__main__' :
	unittest.main()
