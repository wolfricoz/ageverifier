"""Alt account detection, based on members verifying from the same address or the same browser."""
import logging
from dataclasses import dataclass, field

import discord

from databases.current import Users
from databases.transactions.UserTransactions import UserTransactions

# Keeps the formatted list under the 1024 character embed field limit.
MAX_LISTED_ALTS = 20

REASON_IP = "ip"
REASON_DEVICE = "device"

REASON_LABELS = {
	frozenset({REASON_IP}) : "IP",
	frozenset({REASON_DEVICE}) : "device",
	frozenset({REASON_IP, REASON_DEVICE}) : "IP + device",
}


@dataclass
class AltMatch :
	"""Another user who shares a signal with the member, and which signals they share."""
	user: Users
	reasons: set[str] = field(default_factory=set)

	@property
	def uid(self) -> int :
		return self.user.uid


def find_alts(member: discord.Member, ip: str | None, fingerprint: str | None = None) -> list[AltMatch] :
	"""
	Records the member's address and device, and returns other users who last verified from either.

	The two lookups fail independently: a failed lookup is logged and treated as no
	matches, so it never blocks a verification or hides the other signal.

	:param member: the member being verified.
	:param ip: the client address as reported by the website edge, None outside online verification.
	:param fingerprint: the dashboard's hashed browser fingerprint, None outside online verification
		or when the browser could not produce one.
	:return: the matching users with their reasons, empty if there are none.
	"""
	matches: dict[int, AltMatch] = {}

	def add(users: list[Users], reason: str) :
		for user in users :
			matches.setdefault(user.uid, AltMatch(user=user)).reasons.add(reason)

	from api.helpers.VerificationHelpers import check_ip

	try :
		ip_hash = check_ip(member, ip)
		if ip_hash :
			add(UserTransactions().check_duplicate_ips(ip_hash, exclude_uid=member.id), REASON_IP)
	except Exception as e :
		logging.error(f"Duplicate IP check failed for {member.id}: {e}", exc_info=True)

	try :
		fingerprint_digest = check_fingerprint(member, fingerprint)
		if fingerprint_digest :
			add(UserTransactions().check_duplicate_fingerprints(fingerprint_digest, exclude_uid=member.id), REASON_DEVICE)
	except Exception as e :
		logging.error(f"Duplicate device check failed for {member.id}: {e}", exc_info=True)

	return list(matches.values())


def check_fingerprint(member: discord.Member, fingerprint: str | None) -> str | None :
	"""
	Records the device the member verified from, and returns its digest.

	Mirrors check_ip: a first time website verification can arrive before the member has
	a row, so there may be nothing to record against yet, but the digest is still returned
	so the member can be matched against existing users either way.

	:return: the digest, or None if there was no usable fingerprint.
	"""
	from classes.iphash import hash_fingerprint

	digest = hash_fingerprint(fingerprint)
	if digest is None :
		return None

	if UserTransactions().get_user(member.id) is not None :
		UserTransactions().update_user(member.id, device_fingerprint=fingerprint)

	return digest


def format_alts(alts: list[AltMatch] | None) -> str | None :
	"""
	Formats alts as a mention list for an embed field, each with what it matched on.

	Mentions by id rather than guild.get_member, so alts that already left the server still show.

	:return: the formatted list, or None if there are no alts so the field is skipped.
	"""
	if not alts :
		return None
	alt_names = "\n".join(
		f" - <@{alt.uid}> ({REASON_LABELS.get(frozenset(alt.reasons), 'match')})"
		for alt in alts[:MAX_LISTED_ALTS]
	)
	if len(alts) > MAX_LISTED_ALTS :
		alt_names += f"\n...and {len(alts) - MAX_LISTED_ALTS} more"
	return alt_names
