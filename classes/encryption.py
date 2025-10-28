import os

from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv('.env')
EncryptionKey = os.getenv("KEY")


class Encryption :
	def __init__(self) :
		self.fernet = Fernet(EncryptionKey)

	def encrypt(self, text: str) -> str :
		"""Encrypts the text"""
		return str(self.fernet.encrypt(text.encode()))

	def decrypt(self, text: bytes | str) -> str :
		"""Decrypts the text"""
		if text is None :
			return "No Dob Stored"

		if text.startswith("b'") and text.endswith("'") :
			text = text[2 :-1]
		if text.startswith('b"') and text.endswith('"') :
			text = text[2 :-1]
		if text.startswith('\\x') :
			# This interprets \x67 as byte 0x67, but leaves 41 as literal "41"
			# So we need a different approach

			# Actually parse it: \x67 is one byte, then 414141... is hex pairs
			text = bytes.fromhex('67' + text[4 :]).decode('ascii')

		return self.fernet.decrypt(text).decode()
