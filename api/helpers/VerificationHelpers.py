from classes.iphash import hash_ip
from databases.current import Users
from databases.transactions.UserTransactions import UserTransactions


def check_ip(user: Users, current_ip: str) -> bool :
	"""
	Records the address the user verified from, and reports whether it changed.

	The write happens on every call, not only on a change, so ip_recorded_at
	tracks when the address was last seen. An address still in active use
	therefore survives the retention sweep, while one the ISP has rotated away
	from ages out.

	A changed address is a weak signal on its own, since dynamic addresses rotate
	constantly; the value is in matching one user's digests against another's.

	:param user: the user being verified.
	:param current_ip: the client address as reported by the website edge.
	:return: True if this is a different address than the one on record.
	"""
	hashes = hash_ip(current_ip)
	if hashes is None :
		return False

	changed = user.ip_hash != hashes["ip_hash"]
	UserTransactions().update_user(user.uid, ip_address=current_ip)
	return changed


def check_alts(user: Users) -> bool:
	# TODO: still a stub. This is the direction the digests are actually for:
	#  match this user's ip_hash (same host) or ip_prefix_* (same ISP pool) against
	#  other users, recent first, and raise an id check rather than acting on it.
	pass
