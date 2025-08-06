from enum import Enum


class StringStorage(str, Enum):
	WHITELIST_ERROR = "⛔ This server is not whitelisted ⛔"
	NO_SHARE_REMINDER = "-# ⚠️ Reminder: users' date of birth is sensitive information and must not be shared with non-whitelisted servers or individuals without proper authorization from Age Verifier management."

	def __str__(self) :
		return self.value