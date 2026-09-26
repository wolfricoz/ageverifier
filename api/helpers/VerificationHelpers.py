import logging
from pathlib import Path

import discord

from classes.iphash import hash_ip
from databases.current import Users
from databases.transactions.UserTransactions import UserTransactions
from resources.data.config_variables import ASN_NON_RESIDENTIAL_POINTS, KNOWN_VPN_POINTS

ASN_BLACKLIST_PATH = Path(__file__).resolve().parents[2] / "resources" / "data" / "asn_blacklist.txt"


def load_asn_blacklist(path: Path = ASN_BLACKLIST_PATH) -> frozenset[int] :
	"""
	Reads the hosting/datacenter ASN list into a set, once, at import.

	A missing file raises rather than returning an empty set: an empty list would
	quietly score every datacenter address as residential.
	"""
	asns = set()
	with open(path, encoding="utf-8") as f :
		for line in f :
			value = line.split("#", 1)[0].strip()
			if value.isdigit() :
				asns.add(int(value))
	logging.info(f"Loaded {len(asns)} non-residential ASNs")
	return frozenset(asns)


ASN_BLACKLIST = load_asn_blacklist()


def check_ip(member: discord.Member, current_ip: str) -> str | None :
	"""
	Records the address the member verified from, and returns its digest.

	The write happens on every call, not only when the address changed, so
	ip_recorded_at tracks when it was last seen. An address still in active use
	therefore survives the retention sweep, while one the ISP has rotated away
	from ages out.

	The returned digest is what alt detection matches on; a changed address is a
	weak signal by itself, since dynamic addresses rotate constantly.

	:param member: the member being verified.
	:param current_ip: the client address as reported by the website edge.
	:return: the digest of the address, or None if there was no usable address.
	"""
	hashes = hash_ip(current_ip)
	if hashes is None :
		return None

	# A first time website verification reaches here before the member has a row,
	# so there may be nothing to record against yet. The digest is still returned
	# so the caller can match this address against existing users either way.
	user: Users = UserTransactions().get_user(member.id)
	if user is not None :
		UserTransactions().update_user(user.uid, ip_address=current_ip)

	return hashes["ip_hash"]


def check_asn(asn: int | None, vpn: bool = False) -> int :
	"""
	Scores how likely it is that the member is not verifying from their own connection.

	- The ASN belongs to a hosting, datacenter or VPN provider, so it is not a
	  residential connection: ASN_NON_RESIDENTIAL_POINTS.
	- The address is a known VPN, as flagged by the website's IP2Proxy lookup:
	  KNOWN_VPN_POINTS.

	The two stack, since most VPN exits also sit in a datacenter ASN. An unknown ASN
	scores nothing rather than counting as suspicious, because the list only covers
	providers we know about and a missing lookup says nothing about the member.

	:param asn: the autonomous system number of the address, or None if unknown.
	:param vpn: whether the website flagged the address as a known VPN.
	:return: the points to add, 0 if neither applies.
	"""
	points = 0

	if asn is not None and asn in ASN_BLACKLIST :
		points += ASN_NON_RESIDENTIAL_POINTS

	if vpn :
		points += KNOWN_VPN_POINTS

	return points
