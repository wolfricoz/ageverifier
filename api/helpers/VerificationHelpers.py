import logging

import discord

from classes.iphash import hash_ip
from databases.current import Users
from databases.transactions.UserTransactions import UserTransactions


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
