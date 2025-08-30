import logging
import os

from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv('.env')
EncryptionKey = os.getenv("KEY")


class Encryption:
    def __init__(self):
        self.fernet = Fernet(EncryptionKey)

    def encrypt(self, text: str) -> bytes:
        """Encrypts the text"""
        return self.fernet.encrypt(text.encode())

    def decrypt(self, text: bytes | str) -> str:
        """Decrypts the text"""
        if text is None:
            return "No Dob Stored"
        logging.info(f"Decrypting {text}")
        logging.info(self.fernet)
        logging.info(EncryptionKey)
        return self.fernet.decrypt(text).decode()
