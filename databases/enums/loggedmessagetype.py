import enum


class LoggedMessageType(enum.Enum) :
	"""What kind of message a logged_messages row points at.

	Recorded so a cleanup can tell the entries apart - a verification log entry and an ID check
	post live in different channels and carry different data, and being able to select on that
	beats guessing from the channel id.
	"""
	LOBBY_LOG = "LOBBY_LOG"
	"""Verification entry in age_log, or reverify_age_log for a reverification."""

	APPROVAL = "APPROVAL"
	"""Approval request in approval_channel, carrying the age and (on whitelisted guilds) the dob."""

	ID_CHECK = "ID_CHECK"
	"""ID check post in verification_failure_log."""

	AGE_LOG = "AGE_LOG"
	"""Staff-driven add/update/delete entry written to age_log by the database commands."""

	def __str__(self) :
		return self.value
