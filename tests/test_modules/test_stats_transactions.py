import unittest
from datetime import datetime, timedelta

from sqlalchemy import Select

from databases.Generators.guildgenerator import guildgenerator
from databases.Generators.uidgenerator import uidgenerator
from databases.current import IdVerification, JoinHistory, WebsiteData, create_bot_database, drop_bot_database
from databases.enums.joinhistorystatus import JoinHistoryStatus
from databases.transactions.HistoryTransactions import JoinHistoryTransactions
from databases.transactions.StatsTransactions import StatsTransactions
from databases.transactions.UserTransactions import UserTransactions
from databases.transactions.WebsiteDataTransactions import WebsiteDataTransactions


class TestStatsTransactions(unittest.TestCase) :

	def setUp(self) -> None :
		create_bot_database()
		self.stats = StatsTransactions()
		self.gid = guildgenerator().create().guild
		self.end = datetime.now() + timedelta(minutes=1)
		self.start = self.end - timedelta(days=7)

	def tearDown(self) -> None :
		drop_bot_database()

	def _history(self, status, created: datetime, verified: datetime = None, updated: datetime = None) :
		uid = uidgenerator().create()
		UserTransactions().add_user_empty(uid)
		entry = JoinHistoryTransactions().add(uid, self.gid, status, verification_date=verified, created_at=created)
		with self.stats.createsession() as session :
			row = session.scalar(Select(JoinHistory).where(JoinHistory.id == entry.id))
			row.last_updated = updated or created
			self.stats.commit(session)
		return uid

	def test_funnel_splits_this_week_from_last_week(self) :
		now = datetime.now()
		self._history(JoinHistoryStatus.NEW, now - timedelta(days=1))
		self._history(JoinHistoryStatus.SUCCESS, now - timedelta(days=2), verified=now - timedelta(days=2))
		self._history(JoinHistoryStatus.VERIFIED, now - timedelta(days=3), verified=now - timedelta(days=1))
		self._history(JoinHistoryStatus.IDCHECK, now - timedelta(days=2))
		self._history(JoinHistoryStatus.FAILED, now - timedelta(days=10), updated=now - timedelta(days=1))
		self._history(JoinHistoryStatus.SUCCESS, now - timedelta(days=9), verified=now - timedelta(days=9))

		funnel = self.stats.funnel(self.start, self.end)
		previous = self.stats.funnel(self.start - timedelta(days=7), self.start)

		self.assertEqual(funnel, {"joins" : 4, "approved" : 2, "flagged" : 1, "left" : 1, "pending" : 1})
		self.assertEqual(previous["joins"], 2)
		self.assertEqual(previous["approved"], 1)

	def test_time_to_verify_median(self) :
		now = datetime.now()
		for hours in (1, 2, 3) :
			self._history(JoinHistoryStatus.SUCCESS, now - timedelta(days=1, hours=hours),
			              verified=now - timedelta(days=1))

		result = self.stats.time_to_verify(self.start, self.end)

		self.assertAlmostEqual(result["median"], 2 * 3600, delta=1)

	def test_time_to_verify_without_approvals(self) :
		self.assertEqual(self.stats.time_to_verify(self.start, self.end), {"median" : None, "p90" : None})

	def test_peaks_and_top_servers(self) :
		verified = datetime.now().replace(minute=0, second=0, microsecond=0) - timedelta(days=1)
		self._history(JoinHistoryStatus.SUCCESS, verified - timedelta(hours=1), verified=verified)
		self._history(JoinHistoryStatus.SUCCESS, verified - timedelta(hours=1), verified=verified)

		peaks = self.stats.peak_times(self.start, self.end)
		top = self.stats.top_servers(self.start, self.end)

		self.assertEqual(peaks["hour"], (verified.hour, 2))
		# Postgres counts Sunday as 0, Python counts Monday as 0.
		self.assertEqual(peaks["weekday"], ((verified.weekday() + 1) % 7, 2))
		self.assertEqual(len(top), 1)
		self.assertEqual(top[0][1], 2)

	def test_website_funnel(self) :
		now = datetime.now()
		uid = uidgenerator().create()
		UserTransactions().add_user_empty(uid)
		website = WebsiteDataTransactions()
		uuids = [website.create(uid, self.gid) for _ in range(3)]
		with self.stats.createsession() as session :
			rows = session.scalars(Select(WebsiteData).where(WebsiteData.uuid.in_(uuids)).order_by(WebsiteData.id)).all()
			rows[0].opened = now
			rows[1].opened = now
			rows[1].reminded = now
			rows[1].verified = now + timedelta(seconds=30)
			self.stats.commit(session)

		funnel = self.stats.website_funnel(self.start, self.end)

		self.assertEqual(funnel, {"created" : 3, "opened" : 2, "verified" : 1, "reminded" : 1,
		                          "after_reminder" : 1, "abandoned" : 1})

	def test_website_funnel_for_one_guild(self) :
		other_gid = guildgenerator().create().guild
		uid = uidgenerator().create()
		UserTransactions().add_user_empty(uid)
		website = WebsiteDataTransactions()
		mine = website.create(uid, self.gid)
		website.create(uid, other_gid)
		website.set_opened(mine, uid, self.gid)

		funnel = self.stats.website_funnel(self.start, self.end, self.gid)
		everywhere = self.stats.website_funnel(self.start, self.end)

		self.assertEqual(funnel["created"], 1)
		self.assertEqual(funnel["opened"], 1)
		self.assertEqual(funnel["abandoned"], 1)
		self.assertEqual(everywhere["created"], 2)

	def test_website_funnel_for_guild_without_links(self) :
		funnel = self.stats.website_funnel(self.start, self.end, self.gid)

		self.assertEqual(set(funnel.values()), {0})

	def test_id_check_backlog(self) :
		now = datetime.now()
		uid = uidgenerator().create()
		UserTransactions().add_user_empty(uid)
		with self.stats.createsession() as session :
			session.add(IdVerification(uid=uid, idcheck=True, idverified=False,
			                           idmessagecreated=now - timedelta(days=2)))
			self.stats.commit(session)

		result = self.stats.id_checks(self.start, self.end, now)

		self.assertEqual(result["uploads"], 1)
		self.assertEqual(result["backlog"], 1)
		self.assertAlmostEqual(result["oldest_upload_age"].total_seconds(), 2 * 86400, delta=5)

	def test_server_and_user_stats(self) :
		now = datetime.now()
		servers = self.stats.server_stats(self.start, self.end, now)
		users = self.stats.user_stats(self.start, self.end, now)

		self.assertEqual(servers["active"], 1)
		self.assertEqual(servers["joined"], 1)
		self.assertGreaterEqual(users["total"], 1)
