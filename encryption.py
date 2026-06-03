"""
encryption.py - AES encryption/decryption using Fernet (AES-128-CBC + HMAC)
Key derivation via PBKDF2-HMAC-SHA256
"""

import os
import base64
import hashlib
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend


PBKDF2_ITERATIONS = 480_000  # OWASP 2023 recommendation


def derive_key(master_password: str, salt: bytes) -> bytes:
    """Derive a 32-byte key from master_password + salt using PBKDF2."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
        backend=default_backend(),
    )
    raw_key = kdf.derive(master_password.encode("utf-8"))
    # Fernet requires a URL-safe base64-encoded 32-byte key
    return base64.urlsafe_b64encode(raw_key)


def hash_password(master_password: str, salt: bytes) -> str:
    """Return a hex-encoded PBKDF2 hash for storing/comparing the master password."""
    dk = hashlib.pbkdf2_hmac(
        "sha256",
        master_password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
    )
    return dk.hex()


def generate_salt() -> bytes:
    return os.urandom(32)


def encrypt_data(plaintext: bytes, fernet_key: bytes) -> bytes:
    f = Fernet(fernet_key)
    return f.encrypt(plaintext)


def decrypt_data(ciphertext: bytes, fernet_key: bytes) -> bytes:
    f = Fernet(fernet_key)
    return f.decrypt(ciphertext)


def encrypt_file_bytes(data: bytes, fernet_key: bytes) -> bytes:
    return encrypt_data(data, fernet_key)


def decrypt_file_bytes(data: bytes, fernet_key: bytes) -> bytes:
    return decrypt_data(data, fernet_key)
