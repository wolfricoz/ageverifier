import hashlib
import hmac
import ipaddress
import logging
import os
import sys

from dotenv import load_dotenv

load_dotenv('.env')
IpHashKey = os.getenv("IP_HASH_KEY")
if not IpHashKey :
	sys.exit("You must define an environment variable called IP_HASH_KEY")

# Column name -> (IPv4 prefix length, IPv6 prefix length).
#
# We store several widths because the address itself is never kept, so the pool
# boundary cannot be recomputed later. A /24 is the common ISP allocation block,
# but rotation pools are often wider, and picking wrong would be permanent.
#
# The IPv6 sizes are the equivalent boundaries, not the same numbers: /64 is one
# subscriber's subnet and /48 their allocation. Hashing a full IPv6 address is
# close to useless for correlation because privacy extensions rotate the host
# portion, so the prefixes carry the signal there.
PREFIX_SIZES = {
	"ip_prefix_24" : (24, 64),
	"ip_prefix_20" : (20, 48),
	"ip_prefix_16" : (16, 32),
}


def _digest(value: str) -> str :
	"""HMACs one normalised value with the peppered key."""
	return hmac.new(IpHashKey.encode(), value.encode(), hashlib.sha256).hexdigest()


def hash_fingerprint(fingerprint: str | None) -> str | None :
	"""
	Peppers the website's device fingerprint before it is stored.

	The dashboard already sends a SHA-256 of the browser traits, but a bare hash of a
	small, guessable input can be matched against a precomputed table. HMACing it with
	the same key as the addresses means a leaked column is useless on its own.

	:param fingerprint: 64 hex characters from the dashboard, or None.
	:return: the digest, or None if the value was missing or malformed.
	"""
	if not fingerprint :
		return None
	value = fingerprint.strip().lower()
	if len(value) != 64 or any(c not in "0123456789abcdef" for c in value) :
		logging.warning("Discarded a malformed device fingerprint before hashing.")
		return None
	return _digest(value)


def hash_ip(raw_ip: str) -> dict | None :
	"""
	Turns a raw address into the set of hashes we actually store.

	Returns a dict of column name -> hex digest, or None if the address was
	malformed. The raw address is never stored, logged or returned; equality on
	these digests is what powers alt detection, and the prefix digests are what
	survive an ISP rotating a subscriber's address within its pool.

	:param raw_ip: the client address as reported by the website edge.
	:return: dict of column values, or None.
	"""
	try :
		address = ipaddress.ip_address(raw_ip.strip())
	except (AttributeError, ValueError) :
		# Deliberately does not log the value, it is still personal data.
		logging.warning("Discarded a malformed IP address before hashing.")
		return None

	# .compressed normalises IPv6 shorthand and casing, otherwise the same host
	# would digest differently depending on how the caller formatted it.
	hashes = {"ip_hash" : _digest(address.compressed)}

	for field, sizes in PREFIX_SIZES.items() :
		bits = sizes[0] if address.version == 4 else sizes[1]
		network = ipaddress.ip_network(f"{address.compressed}/{bits}", strict=False)
		hashes[field] = _digest(network.compressed)

	return hashes
