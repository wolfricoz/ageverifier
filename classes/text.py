"""Small wording helpers for messages the bot sends."""


def plural(count: int, word: str) -> str :
	"""'1 day', '2 days': messages used to say '1 days'."""
	return f"{count} {word}" if count == 1 else f"{count} {word}s"
