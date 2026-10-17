import unittest

from modules.Stats import website_funnel_embed


def _funnel(**overrides) :
	funnel = {"created" : 10, "opened" : 8, "verified" : 5, "reminded" : 2, "after_reminder" : 1, "abandoned" : 3}
	funnel.update(overrides)
	return funnel


class TestWebsiteFunnelEmbed(unittest.TestCase) :

	def test_funnel_lines(self) :
		embed = website_funnel_embed(_funnel(), 30)
		funnel, reminders = (field.value for field in embed.fields)

		self.assertIn("30 day(s)", embed.description)
		self.assertIn("Links created: **10**", funnel)
		self.assertIn("Opened the page: **8** (80%)", funnel)
		self.assertIn("Never opened: **2** (20%)", funnel)
		self.assertIn("Verified: **5** (50%)", funnel)
		self.assertIn("Opened but not finished: **3** (38% of opened)", funnel)
		self.assertIn("Finished after the reminder: **1** (50%)", reminders)

	def test_without_reminders_points_to_the_setting(self) :
		embed = website_funnel_embed(_funnel(reminded=0, after_reminder=0), 7)

		self.assertIn("/config verification_reminder", embed.fields[1].value)

	def test_empty_funnel(self) :
		empty = dict.fromkeys(_funnel(), 0)

		embed = website_funnel_embed(empty, 7)

		self.assertIn("Opened the page: **0** (—)", embed.fields[0].value)
