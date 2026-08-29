import unittest

import discord

from classes.toolbox import Toolbox
from databases.enums.loggedmessagetype import LoggedMessageType


class FakeMessage :
	def __init__(self, content="", embeds=()) :
		self.content = content
		self.embeds = list(embeds)


UID = 123456789012345678
OWNER = 999999999999999999


def id_check_embed(uid) :
	embed = discord.Embed(title="ID Check Required", description="staff notice")
	embed.set_footer(text=str(uid))
	return embed


def approval_embed() :
	# The approval embed's footer is a uuid, not a user id.
	embed = discord.Embed(title="Verification")
	embed.set_footer(text="6d3f8a1e-0000-4c2b-9f7a-1b2c3d4e5f60")
	return embed


class TestToolboxIdentify(unittest.TestCase) :
	"""Covers reading a user and a type back out of the messages the bot posted historically."""

	def test_lobby_log(self) :
		message = FakeMessage(content=(
			f"user: <@{UID}>\nAge: 22 \nUser info: \nUID: {UID} \n"
			f"Joined at: 01/01/2025 12:00:00 AM \nStaff: someone"))
		self.assertEqual(Toolbox().identify_message(message), (UID, LoggedMessageType.LOBBY_LOG))

	def test_lobby_log_with_id_verified_prefix(self) :
		message = FakeMessage(content=(
			f"**ID VERIFIED**\nuser: <@{UID}>\nAge: 22 \nUser info: \nUID: {UID} \nStaff: someone"))
		self.assertEqual(Toolbox().identify_message(message), (UID, LoggedMessageType.LOBBY_LOG))

	def test_age_log_entry(self) :
		message = FakeMessage(content=f"USER ADDED\nUID: {UID}\nEntry updated by: someone")
		self.assertEqual(Toolbox().identify_message(message), (UID, LoggedMessageType.AGE_LOG))

	def test_id_check_from_embed_footer(self) :
		message = FakeMessage(content="-# Lobby Debug] Age: 16 dob 01/01/2009",
		                      embeds=[id_check_embed(UID)])
		self.assertEqual(Toolbox().identify_message(message), (UID, LoggedMessageType.ID_CHECK))

	def test_id_check_from_content(self) :
		message = FakeMessage(content=f"-# Lobby Debug] Age: 16 dob 01/01/2009 userid: <@{UID}>")
		self.assertEqual(Toolbox().identify_message(message), (UID, LoggedMessageType.ID_CHECK))

	def test_custom_id_check(self) :
		message = FakeMessage(content=f"-# Custom idcheck for <@{UID}>")
		self.assertEqual(Toolbox().identify_message(message), (UID, LoggedMessageType.ID_CHECK))

	def test_approval_post(self) :
		message = FakeMessage(content=f"<@{UID}> \n-# All timestamps are (mm/dd/yyyy) ",
		                      embeds=[approval_embed()])
		self.assertEqual(Toolbox().identify_message(message), (UID, LoggedMessageType.APPROVAL))

	def test_owner_ping_does_not_steal_the_id_check(self) :
		# send_check prefixes the owner's mention when ping_owner_on_failure is on. Attributing
		# the post to the owner would make their removal delete somebody else's ID check.
		message = FakeMessage(
			content=f"<@{OWNER}> -# Lobby Debug] Age: 16 dob 01/01/2009 userid: <@{UID}>",
			embeds=[id_check_embed(UID)])
		self.assertEqual(Toolbox().identify_message(message), (UID, LoggedMessageType.ID_CHECK))

	def test_owner_ping_on_custom_id_check(self) :
		message = FakeMessage(content=f"<@{OWNER}>\n-# Custom idcheck for <@{UID}>",
		                      embeds=[id_check_embed(UID)])
		self.assertEqual(Toolbox().identify_message(message), (UID, LoggedMessageType.ID_CHECK))

	def test_ignores_unrelated_messages(self) :
		self.assertIsNone(Toolbox().identify_message(FakeMessage(content="[SECURITY NOTICE] Too many viewers")))
		self.assertIsNone(Toolbox().identify_message(FakeMessage(content="")))
		self.assertIsNone(Toolbox().identify_message(FakeMessage(content=f"<@{UID}> said hello")))
		self.assertIsNone(Toolbox().identify_message(FakeMessage(
			content="A user has requested data removal!", embeds=[discord.Embed(title="x")])))

	def test_role_mention_is_not_read_as_a_user(self) :
		message = FakeMessage(content="<@&555555555555555555> \n-# All timestamps are (mm/dd/yyyy) ",
		                      embeds=[approval_embed()])
		self.assertIsNone(Toolbox().identify_message(message))


if __name__ == "__main__" :
	unittest.main()
