"""One risk score for an online verification, so staff read one number instead of several flags."""
from dataclasses import dataclass, field
from datetime import datetime, timezone

from classes.alts import REASON_DEVICE, REASON_IP, AltMatch
from resources.data.config_variables import (RISK_ACCOUNT_AGE_POINTS, RISK_BANDS, RISK_DEVICE_ALT_POINTS,
                                             RISK_IP_ALT_POINTS, RISK_IP_AND_DEVICE_ALT_POINTS, RISK_MAX,
                                             RISK_VPN_POINTS)


@dataclass
class RiskScore :
	score: int
	band: str
	emoji: str
	reasons: list[str] = field(default_factory=list)

	def format(self) -> str :
		"""The embed field value: the score and band, then what contributed to it."""
		summary = f"{self.emoji} **{self.score}/{RISK_MAX} · {self.band}**"
		if not self.reasons :
			return f"{summary}\nNo risk signals"
		return f"{summary}\n{' · '.join(self.reasons)}"


def calculate_risk(created_at: datetime, alts: list[AltMatch] | None, vpn: bool, vpn_score: int = 0,
                   now: datetime | None = None) -> RiskScore :
	"""
	Combines the VPN, alt and account age signals into one capped score.

	Alts add points once, for the strongest match among them, rather than per alt: ten
	alts on one shared address are not ten times the evidence. A match on both IP and
	device is the strongest, a device-only match the weakest, because identical phone
	models on the same OS version can share a fingerprint.

	:param created_at: when the member's Discord account was created.
	:param alts: the matches from classes.alts.find_alts.
	:param vpn: whether the website flagged the address for review as a VPN or proxy.
	:param vpn_score: the website's VPN detector score, shown alongside the flag.
	:param now: the current time, for tests.
	"""
	now = now or datetime.now(tz=timezone.utc)
	score = 0
	reasons = []

	if vpn :
		score += RISK_VPN_POINTS
		reasons.append(f"VPN/proxy ({vpn_score}%)" if vpn_score else "VPN/proxy")

	alts = alts or []
	ip_alts = sum(1 for alt in alts if REASON_IP in alt.reasons)
	device_alts = sum(1 for alt in alts if REASON_DEVICE in alt.reasons)
	if any(alt.reasons >= {REASON_IP, REASON_DEVICE} for alt in alts) :
		score += RISK_IP_AND_DEVICE_ALT_POINTS
	elif ip_alts :
		score += RISK_IP_ALT_POINTS
	elif device_alts :
		score += RISK_DEVICE_ALT_POINTS
	if ip_alts :
		reasons.append(f"{ip_alts} IP alt{'s' if ip_alts != 1 else ''}")
	if device_alts :
		reasons.append(f"{device_alts} device alt{'s' if device_alts != 1 else ''}")

	account_age_days = max(0, (now - created_at).days)
	for max_days, points in RISK_ACCOUNT_AGE_POINTS :
		if account_age_days < max_days :
			score += points
			reasons.append(f"account {account_age_days} day{'s' if account_age_days != 1 else ''} old")
			break

	score = min(score, RISK_MAX)
	for lowest, band, emoji in RISK_BANDS :
		if score >= lowest :
			return RiskScore(score=score, band=band, emoji=emoji, reasons=reasons)
	raise ValueError("RISK_BANDS must include a band starting at 0")
