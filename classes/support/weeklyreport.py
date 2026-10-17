"""The weekly developer stats report, posted to the DEV channel on Sundays by modules.Tasks.

Everything here comes from data the bot already keeps: the database (databases.transactions.StatsTransactions),
the log files (classes.support.logreader) and the quick leave files (classes.support.quickleaves). collect() gathers it, build_embeds() only
formats it so it can be tested without a bot, and send() posts it.
"""
import asyncio
import logging
import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

import discord
from matplotlib import pyplot as plt

from classes.charts import JoinHistoryCharts
from classes.support import quickleaves
from classes.support.logreader import read_records
from databases.transactions.HistoryTransactions import JoinHistoryTransactions
from databases.transactions.ServerTransactions import ServerTransactions
from databases.transactions.StatsTransactions import StatsTransactions
from resources.data.config_variables import QUICK_LEAVE_DAYS, QUICK_LEAVE_DIR, REPORT_TOP_SERVERS

FIELD_LIMIT = 1024
WEEKDAYS = ("Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday")  # Postgres dow order
# Module import happens while the cogs load, which is close enough to the bot's start for an uptime figure.
_loaded = datetime.now(tz=timezone.utc)


@dataclass
class LogSummary :
	errors: int = 0
	warnings: int = 0
	top_errors: list[tuple[str, int]] = field(default_factory=list)


@dataclass
class WeeklyReport :
	start: datetime
	end: datetime
	funnel: dict
	previous_funnel: dict
	time_to_verify: dict
	peaks: dict
	top_servers: list[tuple[str, int]]
	website: dict
	previous_website: dict
	id_checks: dict
	servers: dict
	users: dict
	invalid_invites: int
	guilds_connected: int
	latency_ms: int | None
	online_since: datetime
	logs: LogSummary
	quick_leaves: list[quickleaves.SavedQuickLeave] = field(default_factory=list)


def summarise_logs(start: datetime, paths: list[str] = None) -> LogSummary :
	"""Counts ERROR and WARNING lines logged since start, and the most common error messages."""
	summary = LogSummary()
	messages = Counter()
	for record in read_records(start, paths) :
		if record.level == "WARNING" :
			summary.warnings += 1
		elif record.level in ("ERROR", "CRITICAL") :
			summary.errors += 1
			# Ids and counts would make every occurrence of the same error unique.
			messages[re.sub(r"\d+", "#", record.message.strip())[:90]] += 1
	summary.top_errors = messages.most_common(3)
	return summary


def _collect_database(start: datetime, end: datetime) -> dict :
	stats = StatsTransactions()
	previous = start - (end - start)
	return {
		"funnel"           : stats.funnel(start, end),
		"previous_funnel"  : stats.funnel(previous, start),
		"time_to_verify"   : stats.time_to_verify(start, end),
		"peaks"            : stats.peak_times(start, end),
		"top_servers"      : stats.top_servers(start, end, REPORT_TOP_SERVERS),
		"website"          : stats.website_funnel(start, end),
		"previous_website" : stats.website_funnel(previous, start),
		"id_checks"        : stats.id_checks(start, end, end),
		"servers"          : stats.server_stats(start, end, end),
		"users"            : stats.user_stats(start, end, end),
		"invalid_invites"  : len(ServerTransactions().get_invalid_invites()),
	}


async def collect(bot, now: datetime = None, days: int = 7) -> WeeklyReport :
	end = now or datetime.now()
	start = end - timedelta(days=days)
	data = await asyncio.to_thread(_collect_database, start, end)
	logs = await asyncio.to_thread(summarise_logs, start)
	quick_leaves = await asyncio.to_thread(quickleaves.saved_since, start)
	latency = bot.latency
	return WeeklyReport(
		start=start, end=end, **data,
		guilds_connected=len(bot.guilds),
		latency_ms=round(latency * 1000) if latency == latency and latency != float("inf") else None,
		online_since=_loaded,
		logs=logs,
		quick_leaves=quick_leaves,
	)


def delta(current: int, previous: int) -> str :
	"""The change against the previous week, e.g. '▲ 12%'."""
	if not previous :
		return "—" if not current else "new"
	change = round((current - previous) / previous * 100)
	if change == 0 :
		return "± 0%"
	return f"{'▲' if change > 0 else '▼'} {abs(change)}%"


def rate(part: int, whole: int) -> str :
	return f"{part / whole:.0%}" if whole else "—"


def duration(seconds: float | None) -> str :
	if seconds is None :
		return "—"
	minutes = int(seconds // 60)
	days, minutes = divmod(minutes, 60 * 24)
	hours, minutes = divmod(minutes, 60)
	if days :
		return f"{days}d {hours}h"
	if hours :
		return f"{hours}h {minutes}m"
	return f"{minutes}m"


def _field(embed: discord.Embed, name: str, lines: list[str]) :
	value = "\n".join(lines) or "—"
	if len(value) > FIELD_LIMIT :
		value = value[:FIELD_LIMIT - 1] + "…"
	embed.add_field(name=name, value=value, inline=False)


def _row(label: str, current: int, previous: int = None) -> str :
	if previous is None :
		return f"{label}: **{current:,}**"
	return f"{label}: **{current:,}** ({delta(current, previous)})"


def build_embeds(report: WeeklyReport) -> list[discord.Embed] :
	period = f"{report.start:%b %d} – {report.end:%b %d, %Y}"
	f, pf = report.funnel, report.previous_funnel
	outcomes = f["approved"] + f["flagged"] + f["left"]

	verification = discord.Embed(title="📊 Weekly stats", description=f"{period} · change vs the week before",
	                             color=discord.Color.blue())
	_field(verification, "Verification funnel", [
		_row("Joins", f["joins"], pf["joins"]),
		_row("Approved", f["approved"], pf["approved"]),
		_row("Flagged for ID check", f["flagged"], pf["flagged"]),
		_row("Left the lobby", f["left"], pf["left"]),
		f"Approval rate: **{rate(f['approved'], outcomes)}** "
		f"(last week {rate(pf['approved'], pf['approved'] + pf['flagged'] + pf['left'])})",
		_row("Waiting in lobbies now", f["pending"]),
	])
	peaks = report.peaks
	_field(verification, "Speed & peaks", [
		f"Time to verify: median **{duration(report.time_to_verify['median'])}**, "
		f"p90 **{duration(report.time_to_verify['p90'])}**",
		f"Busiest day: **{WEEKDAYS[peaks['weekday'][0]]}** ({peaks['weekday'][1]:,})" if peaks.get("weekday") else "Busiest day: —",
		f"Busiest hour: **{peaks['hour'][0]:02d}:00** ({peaks['hour'][1]:,})" if peaks.get("hour") else "Busiest hour: —",
	])
	_field(verification, f"Top {len(report.top_servers)} servers by approvals" if report.top_servers else "Top servers",
	       [f"{i}. {discord.utils.escape_markdown(name or 'unknown')[:60]}: **{total:,}**"
	        for i, (name, total) in enumerate(report.top_servers, start=1)])

	w, pw = report.website, report.previous_website
	ids = report.id_checks
	online = discord.Embed(title="🌐 Online & ID verification", color=discord.Color.teal())
	_field(online, "Online verification links", [
		_row("Created", w["created"], pw["created"]),
		f"Opened: **{w['opened']:,}** ({rate(w['opened'], w['created'])} of created)",
		f"Verified: **{w['verified']:,}** ({rate(w['verified'], w['opened'])} of opened, "
		f"last week {rate(pw['verified'], pw['opened'])})",
		f"Opened but never finished: **{w['abandoned']:,}**",
		f"Reminded: **{w['reminded']:,}**, finished after the reminder: **{w['after_reminder']:,}** "
		f"({rate(w['after_reminder'], w['reminded'])})",
	])
	backlog = [
		_row("ID uploads", ids["uploads"]),
		_row("ID checks waiting now", ids["backlog"]),
	]
	if ids["oldest_upload_age"] is not None :
		backlog.append(f"Oldest waiting upload: **{duration(ids['oldest_upload_age'].total_seconds())}** old")
	_field(online, "ID checks", backlog)

	s, u, logs = report.servers, report.users, report.logs
	health = discord.Embed(title="🛠️ Servers, data & health", color=discord.Color.dark_grey())
	drift = s["active"] - report.guilds_connected
	_field(health, "Servers", [
		f"Joined: **{s['joined']:,}** · Left: **{s['left']:,}**",
		f"Active: **{s['active']:,}** ({s['members']:,} members)",
		f"Connected guilds: **{report.guilds_connected:,}**" + (f" ⚠️ {drift:+} vs the database" if drift else ""),
		_row("Premium expiring in 7 days", s["premium_expiring"]),
		_row("Invites needing a refresh", report.invalid_invites),
	])
	quick = [f"**{len(report.quick_leaves)}** server(s) removed the bot within {QUICK_LEAVE_DAYS} days after "
	         f"using it · files in `{QUICK_LEAVE_DIR}`"]
	quick += [f"{discord.utils.escape_markdown(item.name)[:80]}: {item.time_in_server}, {item.commands} command(s)"
	          for item in report.quick_leaves[:5]]
	if len(report.quick_leaves) > 5 :
		quick.append(f"…and {len(report.quick_leaves) - 5} more")
	_field(health, "Quick leaves", quick)
	_field(health, "Users & data", [
		_row("Users on record", u["total"]),
		_row("GDPR removals requested", u["gdpr_requested"]),
		_row("GDPR purges due within 7 days", u["gdpr_due_soon"]),
		f"Warnings: **{u['warnings']:,}** · Watchlist: **{u['watchlist']:,}**",
		_row("Device fingerprints recorded", u["fingerprints"]),
	])
	errors = [
		f"Online since: {discord.utils.format_dt(report.online_since, 'R')}",
		f"Latency: **{report.latency_ms} ms**" if report.latency_ms is not None else "Latency: —",
		f"Logged errors: **{logs.errors:,}** · warnings: **{logs.warnings:,}**",
	]
	errors += [f"`{count}×` {discord.utils.escape_markdown(message)}" for message, count in logs.top_errors]
	_field(health, "Bot health", errors)
	health.set_footer(text="Flagged/left use join_history.last_updated, since rows are edited in place.")
	return [verification, online, health]


async def send(bot, now: datetime = None) -> bool :
	"""Posts the report to the DEV channel. Returns False when it could not be posted."""
	channel = bot.get_channel(bot.DEV)
	if channel is None :
		logging.warning("Weekly report skipped: the DEV channel could not be found.")
		return False
	report = await collect(bot, now)
	embeds = build_embeds(report)

	chart = None
	try :
		data = await asyncio.to_thread(JoinHistoryTransactions().join_leave_graph_data, None, 7)
		chart = JoinHistoryCharts(data, 7).getBarChart()
		plt.close("all")
	except Exception as e :
		# The numbers are still worth posting without the picture.
		logging.error(f"Weekly report chart failed: {e}", exc_info=True)
		chart = None

	try :
		files = [discord.File(chart.filename, filename=chart.filename)] if chart and chart.filename else []
		await channel.send(embeds=embeds, files=files)
		return True
	except Exception as e :
		logging.error(f"Weekly report could not be sent: {e}", exc_info=True)
		return False
	finally :
		if chart and chart.filename :
			chart.clean_up_chart()
