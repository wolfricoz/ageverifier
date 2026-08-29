import unittest

import discord

from views.buttons.gdprremoval import GDPRRemoval


class FakeMessage :
	"""Stands in for discord.Message: mentions_user only reads content and embeds."""

	def __init__(self, content="", embeds=()) :
		self.content = content
		self.embeds = list(embeds)


class TestGDPRRemovalMatching(unittest.TestCase) :
	"""Covers which messages a GDPR removal will delete from a guild's log channels."""

	uid = 123456789012345678
	other_uid = 999999999999999999

	def footer_embed(self, uid) :
		"""An ID check post, which carries the user id in the embed footer."""
		embed = discord.Embed(title="ID Check Required", description="staff notice")
		embed.set_footer(text=str(uid))
		return embed

	def test_matches_message_content(self) :
		message = FakeMessage(content=f"user: <@{self.uid}>\nAge: 22")
		self.assertTrue(GDPRRemoval.mentions_user(message, self.uid))

	def test_matches_embed_footer(self) :
		# The old content-only check missed these, leaving ID check posts behind.
		message = FakeMessage(content="Lobby Debug]", embeds=[self.footer_embed(self.uid)])
		self.assertTrue(GDPRRemoval.mentions_user(message, self.uid))

	def test_matches_embed_description(self) :
		embed = discord.Embed(title="A user has requested data removal!",
		                      description=f"<@{self.uid}> has requested that all their data be removed")
		self.assertTrue(GDPRRemoval.mentions_user(FakeMessage(embeds=[embed]), self.uid))

	def test_matches_embed_field(self) :
		embed = discord.Embed(title="x")
		embed.add_field(name="user", value=f"<@{self.uid}>")
		self.assertTrue(GDPRRemoval.mentions_user(FakeMessage(embeds=[embed]), self.uid))

	def test_ignores_other_users(self) :
		self.assertFalse(GDPRRemoval.mentions_user(
			FakeMessage(content=f"user: <@{self.other_uid}>"), self.uid))
		self.assertFalse(GDPRRemoval.mentions_user(
			FakeMessage(embeds=[self.footer_embed(self.other_uid)]), self.uid))

	def test_ignores_messages_without_the_user(self) :
		self.assertFalse(GDPRRemoval.mentions_user(FakeMessage(), self.uid))
		self.assertFalse(GDPRRemoval.mentions_user(FakeMessage(embeds=[discord.Embed()]), self.uid))

	def test_sweeps_every_channel_a_dob_can_reach(self) :
		# A removal that only swept age_log left the age and date of birth sitting in the other
		# three; if a key is dropped from this tuple, data survives the removal.
		self.assertEqual(
			set(GDPRRemoval.LOG_CHANNEL_KEYS),
			{"age_log", "reverify_age_log", "verification_failure_log", "approval_channel"})


if __name__ == "__main__" :
	unittest.main()
