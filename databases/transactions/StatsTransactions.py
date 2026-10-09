"""Read-only queries behind the weekly developer stats report (classes.support.weeklyreport).

Every window method takes a naive [start, end) pair, the same way the rest of the bot compares
against these columns. join_history rows are edited in place when their status changes, so the
outcome counts use last_updated (or verification_date for approvals) rather than created_date.
"""
from datetime import datetime, timedelta

from sqlalchemy import Select, and_, extract, func

from databases.current import IdVerification, JoinHistory, Servers, Users, Warnings, WebsiteData
from databases.enums.joinhistorystatus import JoinHistoryStatus
from databases.transactions.DatabaseTransactions import DatabaseTransactions
from resources.data.config_variables import GDPR_REMOVAL_GRACE_DAYS

APPROVED = (JoinHistoryStatus.SUCCESS, JoinHistoryStatus.VERIFIED)


def _between(column, start: datetime, end: datetime) :
	return and_(column >= start, column < end)


class StatsTransactions(DatabaseTransactions) :

	def funnel(self, start: datetime, end: datetime) -> dict :
		"""Joins and their outcomes inside the window, plus the members still waiting right now."""
		with self.createsession() as session :
			def count(*where) :
				return session.scalar(Select(func.count(JoinHistory.id)).where(*where)) or 0

			return {
				"joins"    : count(_between(JoinHistory.created_date, start, end)),
				"approved" : count(JoinHistory.status.in_(APPROVED),
				                   _between(JoinHistory.verification_date, start, end)),
				"flagged"  : count(JoinHistory.status == JoinHistoryStatus.IDCHECK,
				                   _between(JoinHistory.last_updated, start, end)),
				"left"     : count(JoinHistory.status == JoinHistoryStatus.FAILED,
				                   _between(JoinHistory.last_updated, start, end)),
				"pending"  : count(JoinHistory.status == JoinHistoryStatus.NEW),
			}

	def time_to_verify(self, start: datetime, end: datetime) -> dict :
		"""Median and p90 time from join to approval, in seconds, for approvals in the window."""
		seconds = extract("epoch", JoinHistory.verification_date - JoinHistory.created_date)
		with self.createsession() as session :
			median, p90 = session.execute(
				Select(func.percentile_cont(0.5).within_group(seconds),
				       func.percentile_cont(0.9).within_group(seconds))
				.where(JoinHistory.status.in_(APPROVED),
				       _between(JoinHistory.verification_date, start, end),
				       JoinHistory.verification_date >= JoinHistory.created_date)
			).one()
			return {"median" : median, "p90" : p90}

	def peak_times(self, start: datetime, end: datetime) -> dict :
		"""The weekday (0 = Sunday, Postgres dow) and hour with the most approvals, or None when there were none."""
		result = {}
		with self.createsession() as session :
			for key, part in (("weekday", "dow"), ("hour", "hour")) :
				bucket = extract(part, JoinHistory.verification_date)
				row = session.execute(
					Select(bucket.label("bucket"), func.count(JoinHistory.id).label("total"))
					.where(JoinHistory.status.in_(APPROVED), _between(JoinHistory.verification_date, start, end))
					.group_by("bucket")
					.order_by(func.count(JoinHistory.id).desc())
					.limit(1)
				).first()
				result[key] = (int(row.bucket), row.total) if row else None
		return result

	def top_servers(self, start: datetime, end: datetime, limit: int = 5) -> list[tuple[str, int]] :
		"""The servers with the most approvals in the window, as (name, approvals)."""
		with self.createsession() as session :
			rows = session.execute(
				Select(Servers.name, func.count(JoinHistory.id).label("total"))
				.join(Servers, Servers.guild == JoinHistory.gid)
				.where(JoinHistory.status.in_(APPROVED), _between(JoinHistory.verification_date, start, end))
				.group_by(Servers.guild, Servers.name)
				.order_by(func.count(JoinHistory.id).desc())
				.limit(limit)
			).all()
			return [(row.name, row.total) for row in rows]

	def website_funnel(self, start: datetime, end: datetime) -> dict :
		"""Online verification links created in the window, and how far they got."""
		created = _between(WebsiteData.created_date, start, end)
		with self.createsession() as session :
			def count(*where) :
				return session.scalar(Select(func.count(WebsiteData.id)).where(created, *where)) or 0

			return {
				"created"            : count(),
				"opened"             : count(WebsiteData.opened.is_not(None)),
				"verified"           : count(WebsiteData.verified.is_not(None)),
				"reminded"           : count(WebsiteData.reminded.is_not(None)),
				"after_reminder"     : count(WebsiteData.reminded.is_not(None),
				                             WebsiteData.verified > WebsiteData.reminded),
				"abandoned"          : count(WebsiteData.opened.is_not(None), WebsiteData.verified.is_(None)),
			}

	def id_checks(self, start: datetime, end: datetime, now: datetime) -> dict :
		"""ID uploads in the window, and the ID check queue as it stands right now."""
		waiting = and_(IdVerification.idcheck.is_(True), IdVerification.idverified.is_not(True))
		with self.createsession() as session :
			uploads = session.scalar(Select(func.count(IdVerification.uid))
			                         .where(_between(IdVerification.idmessagecreated, start, end))) or 0
			backlog = session.scalar(Select(func.count(IdVerification.uid)).where(waiting)) or 0
			oldest = session.scalar(Select(func.min(IdVerification.idmessagecreated))
			                        .where(waiting, IdVerification.idmessagecreated.is_not(None)))
			return {"uploads" : uploads, "backlog" : backlog,
			        "oldest_upload_age" : (now - oldest) if oldest else None}

	def server_stats(self, start: datetime, end: datetime, now: datetime) -> dict :
		with self.createsession() as session :
			def count(*where) :
				return session.scalar(Select(func.count(Servers.guild)).where(*where)) or 0

			return {
				"joined"           : count(_between(Servers.created, start, end)),
				"left"             : count(_between(Servers.deleted_at, start, end)),
				"active"           : count(Servers.active.is_(True)),
				"members"          : session.scalar(Select(func.coalesce(func.sum(Servers.member_count), 0))
				                                    .where(Servers.active.is_(True))) or 0,
				"premium_expiring" : count(_between(Servers.premium, now, now + timedelta(days=7))),
			}

	def user_stats(self, start: datetime, end: datetime, now: datetime) -> dict :
		with self.createsession() as session :
			def count(model, *where) :
				return session.scalar(Select(func.count()).select_from(model).where(*where)) or 0

			return {
				"total"             : count(Users, Users.deleted_at.is_(None)),
				"gdpr_requested"    : count(Users, _between(Users.deleted_at, start, end)),
				# Due within the next week: the purge runs GDPR_REMOVAL_GRACE_DAYS after the request.
				"gdpr_due_soon"     : count(Users, Users.deleted_at.is_not(None),
				                            Users.deleted_at < now - timedelta(days=GDPR_REMOVAL_GRACE_DAYS - 7)),
				"warnings"          : count(Warnings, Warnings.type == "WARN",
				                            _between(Warnings.entry, start, end)),
				"watchlist"         : count(Warnings, Warnings.type == "WATCH",
				                            _between(Warnings.entry, start, end)),
				"fingerprints"      : count(Users, _between(Users.fingerprint_recorded_at, start, end)),
			}
