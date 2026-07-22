import os
import sys

from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv('.env')
EncryptionKey = os.getenv("KEY")
if not EncryptionKey:
	sys.exit("You must define an environment variable called KEY")

class Encryption :
	def __init__(self) :
		self.fernet = Fernet(EncryptionKey)

	def encrypt(self, text: str) -> str :
		"""Encrypts the text"""
		# TODO: [BUG] str(bytes) stores the Python repr "b'...'" of the token, not the token itself. This is why decrypt() below has to strip "b'"/'b"' prefixes. Use .decode() to store the raw token. Migrate existing rows before changing.
		return str(self.fernet.encrypt(text.encode()))

	def decrypt(self, text: bytes | str) -> str :
		"""Decrypts the text"""
		# TODO: [BUG] Type hint says text may be bytes, but .startswith("b'") assumes str and would raise TypeError on bytes. Normalise the input type first.
		if text is None :
			return "No Dob Stored"

		# TODO: [QUALITY] This whole prefix-stripping block only exists to undo the str(bytes) mangling in encrypt(). Fix encrypt() and delete this.
		if text.startswith("b'") and text.endswith("'") :
			text = text[2 :-1]
		if text.startswith('b"') and text.endswith('"') :
			text = text[2 :-1]
		# TODO: [BUG] This '\\x' branch is broken by its own admission (see comments) and hard-codes the byte '67'. It will corrupt any token whose repr begins with an escaped byte. Remove once encrypt() stores raw tokens.
		if text.startswith('\\x') :
			# This interprets \x67 as byte 0x67, but leaves 41 as literal "41"
			# So we need a different approach

			# Actually parse it: \x67 is one byte, then 414141... is hex pairs
			text = bytes.fromhex('67' + text[4 :]).decode('ascii')

		return self.fernet.decrypt(text).decode()
