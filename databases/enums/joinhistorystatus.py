import enum


class JoinHistoryStatus(enum.Enum):
	NEW = "NEW"
	FAILED = "FAILED"
	SUCCESS = "SUCCESS"
	IDCHECK = "IDCHECK"
	VERIFIED = "IDVERIFIED"

	def __str__(self):
		return self.value