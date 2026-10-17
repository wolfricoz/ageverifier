import unittest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from classes.alts import REASON_DEVICE, REASON_IP, AltMatch, format_alts
from classes.verification.risk import calculate_risk

NOW = datetime(2026, 9, 28, tzinfo=timezone.utc)
OLD_ACCOUNT = NOW - timedelta(days=400)


def alt(uid: int, *reasons: str) -> AltMatch :
	return AltMatch(user=SimpleNamespace(uid=uid), reasons=set(reasons))


class TestRiskScore(unittest.TestCase) :
	def test_no_signals_is_low(self) :
		risk = calculate_risk(OLD_ACCOUNT, [], vpn=False, now=NOW)
		self.assertEqual((risk.score, risk.band), (0, "Low"))
		self.assertIn("No risk signals", risk.format())

	def test_signals_add_up_into_the_right_band(self) :
		risk = calculate_risk(NOW - timedelta(days=4), [alt(1, REASON_IP)], vpn=True, vpn_score=55, now=NOW)
		# VPN 35 + IP alt 30 + account under 7 days 25
		self.assertEqual((risk.score, risk.band), (90, "High"))
		self.assertEqual(risk.reasons, ["VPN/proxy (55%)", "1 IP alt", "account 4 days old"])

	def test_alts_count_once_for_the_strongest_match(self) :
		ip_only = calculate_risk(OLD_ACCOUNT, [alt(1, REASON_IP), alt(2, REASON_IP), alt(3, REASON_IP)], vpn=False, now=NOW)
		device_only = calculate_risk(OLD_ACCOUNT, [alt(1, REASON_DEVICE)], vpn=False, now=NOW)
		both = calculate_risk(OLD_ACCOUNT, [alt(1, REASON_DEVICE), alt(2, REASON_IP, REASON_DEVICE)], vpn=False, now=NOW)
		self.assertEqual(ip_only.score, 30)
		self.assertEqual(device_only.score, 20)
		self.assertEqual(both.score, 40)
		self.assertEqual(both.reasons, ["1 IP alt", "2 device alts"])

	def test_account_age_uses_the_first_matching_bracket(self) :
		self.assertEqual(calculate_risk(NOW - timedelta(days=20), [], vpn=False, now=NOW).score, 15)
		self.assertEqual(calculate_risk(NOW - timedelta(days=60), [], vpn=False, now=NOW).score, 5)
		self.assertEqual(calculate_risk(NOW - timedelta(days=90), [], vpn=False, now=NOW).score, 0)

	def test_score_is_capped(self) :
		risk = calculate_risk(NOW, [alt(1, REASON_IP, REASON_DEVICE)], vpn=True, now=NOW)
		# 35 + 40 + 25 = 100, exactly at the cap
		self.assertEqual(risk.score, 100)


class TestFormatAlts(unittest.TestCase) :
	def test_each_alt_shows_what_it_matched_on(self) :
		text = format_alts([alt(1, REASON_IP), alt(2, REASON_DEVICE), alt(3, REASON_IP, REASON_DEVICE)])
		self.assertEqual(text, " - <@1> (IP)\n - <@2> (device)\n - <@3> (IP + device)")

	def test_no_alts_skips_the_field(self) :
		self.assertIsNone(format_alts([]))
