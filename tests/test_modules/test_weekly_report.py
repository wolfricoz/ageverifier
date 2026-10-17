import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

from classes.support import weeklyreport
from classes.support.weeklyreport import LogSummary, WeeklyReport, build_embeds, delta, duration, rate, summarise_logs


def _report(**overrides) -> WeeklyReport :
	end = datetime(2026, 9, 27, 12)
	funnel = {"joins" : 10, "approved" : 6, "flagged" : 2, "left" : 2, "pending" : 3}
	website = {"created" : 5, "opened" : 4, "verified" : 2, "reminded" : 1, "after_reminder" : 1, "abandoned" : 2}
	values = dict(
		start=end - timedelta(days=7), end=end,
		funnel=funnel, previous_funnel=dict(funnel, joins=5),
		time_to_verify={"median" : 5400, "p90" : None},
		peaks={"weekday" : (0, 4), "hour" : (21, 3)},
		top_servers=[("A server", 4), ("B*server", 2)],
		website=website, previous_website=dict(website, opened=0),
		id_checks={"uploads" : 1, "backlog" : 2, "oldest_upload_age" : timedelta(days=1, hours=3)},
		servers={"joined" : 1, "left" : 0, "active" : 20, "members" : 5000, "premium_expiring" : 1},
		users={"total" : 900, "gdpr_requested" : 1, "gdpr_due_soon" : 0, "warnings" : 2, "watchlist" : 1,
		       "fingerprints" : 30},
		invalid_invites=3, guilds_connected=19, latency_ms=42,
		online_since=datetime(2026, 9, 20, tzinfo=timezone.utc),
		logs=LogSummary(errors=4, warnings=9, top_errors=[("Something broke #", 3)]),
	)
	values.update(overrides)
	return WeeklyReport(**values)


class TestWeeklyReportFormatting(unittest.TestCase) :

	def test_delta(self) :
		self.assertEqual(delta(10, 5), "▲ 100%")
		self.assertEqual(delta(5, 10), "▼ 50%")
		self.assertEqual(delta(5, 5), "± 0%")
		self.assertEqual(delta(3, 0), "new")
		self.assertEqual(delta(0, 0), "—")

	def test_rate_and_duration(self) :
		self.assertEqual(rate(1, 4), "25%")
		self.assertEqual(rate(1, 0), "—")
		self.assertEqual(duration(None), "—")
		self.assertEqual(duration(90), "1m")
		self.assertEqual(duration(5400), "1h 30m")
		self.assertEqual(duration(2 * 86400 + 3600), "2d 1h")

	def test_build_embeds(self) :
		embeds = build_embeds(_report())

		self.assertEqual(len(embeds), 3)
		self.assertLess(sum(len(embed) for embed in embeds), 6000)
		text = "\n".join(f.value for embed in embeds for f in embed.fields)
		self.assertIn("Joins: **10** (▲ 100%)", text)
		self.assertIn("Approval rate: **60%**", text)
		self.assertIn("Busiest day: **Sunday** (4)", text)
		self.assertIn("B\\*server", text)
		self.assertIn("+1 vs the database", text)
		self.assertIn("1d 3h", text)
		self.assertIn("**0** server(s) removed the bot", text)

	def test_quick_leaves_are_listed(self) :
		saved = [weeklyreport.quickleaves.SavedQuickLeave(f"Server {i}", "2h 5m", 3, "x.txt") for i in range(7)]
		text = "\n".join(f.value for embed in build_embeds(_report(quick_leaves=saved)) for f in embed.fields)

		self.assertIn("**7** server(s)", text)
		self.assertIn("Server 0: 2h 5m, 3 command(s)", text)
		self.assertIn("…and 2 more", text)

	def test_build_embeds_with_an_empty_week(self) :
		empty = {"joins" : 0, "approved" : 0, "flagged" : 0, "left" : 0, "pending" : 0}
		website = dict.fromkeys(("created", "opened", "verified", "reminded", "after_reminder", "abandoned"), 0)
		embeds = build_embeds(_report(funnel=empty, previous_funnel=empty, peaks={"weekday" : None, "hour" : None},
		                              top_servers=[], website=website, previous_website=website,
		                              id_checks={"uploads" : 0, "backlog" : 0, "oldest_upload_age" : None},
		                              latency_ms=None, logs=LogSummary()))

		for embed in embeds :
			for f in embed.fields :
				self.assertTrue(f.value)

	def test_fields_stay_under_the_discord_limit(self) :
		embeds = build_embeds(_report(top_servers=[("x" * 200, i) for i in range(40)]))

		for embed in embeds :
			for f in embed.fields :
				self.assertLessEqual(len(f.value), weeklyreport.FIELD_LIMIT)


class TestSummariseLogs(unittest.TestCase) :

	def test_counts_recent_lines_only(self) :
		now = datetime.now()
		old = (now - timedelta(days=9)).strftime("%Y-%m-%d %H:%M:%S")
		new = (now - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
		lines = [
			f"{old},001:root:ERROR: too old\n",
			f"{new},001:root:ERROR: Failed for user 123\n",
			f"{new},002:root:ERROR: Failed for user 456\n",
			f"{new},003:discord.gateway:WARNING: Shard lagging\n",
			f"{new},004:root:INFO: all good\n",
			"  Traceback line without a timestamp\n",
		]
		with tempfile.TemporaryDirectory() as folder :
			path = os.path.join(folder, "log.txt")
			with open(path, "w", encoding="utf-8") as file :
				file.writelines(lines)

			summary = summarise_logs(now - timedelta(days=7), [path])

		self.assertEqual(summary.errors, 2)
		self.assertEqual(summary.warnings, 1)
		self.assertEqual(summary.top_errors, [("Failed for user #", 2)])

	def test_missing_file_is_skipped(self) :
		summary = summarise_logs(datetime.now(), ["does/not/exist.txt"])

		self.assertEqual(summary.errors, 0)
