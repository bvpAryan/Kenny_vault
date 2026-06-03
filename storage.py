"""
storage.py - Encrypted vault file I/O.

Vault file format (vault.dat):
  Bytes 0-3   : magic "VLT1"
  Bytes 4-35  : 32-byte salt (used for PBKDF2 key derivation + password hash)
  Bytes 36-67 : 32-byte password-hash (hex encoded → stored as raw bytes? No → stored as 64 ASCII chars)
  Actually we store:
    [4]  magic
    [32] salt
    [64] password_hash hex string as UTF-8
    [rest] Fernet-encrypted JSON payload
"""

import os
import json
from pathlib import Path
from typing import Optional

MAGIC = b"VLT1"
SALT_LEN = 32
HASH_LEN = 64  # hex string of 32-byte PBKDF2 result

DATA_DIR = Path(__file__).parent / "data"
VAULT_PATH = DATA_DIR / "vault.dat"
FILES_DIR = DATA_DIR / "encrypted_files"

EMPTY_VAULT = {
    "passwords": [],
    "notes": [],
    "files": [],
}


def ensure_dirs():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    FILES_DIR.mkdir(parents=True, exist_ok=True)


def vault_exists() -> bool:
    return VAULT_PATH.exists()


def create_vault(master_password: str) -> bytes:
    """Create a new vault, return the derived fernet key."""
    from encryption import generate_salt, hash_password, derive_key, encrypt_data

    ensure_dirs()
    salt = generate_salt()
    pw_hash = hash_password(master_password, salt)
    fernet_key = derive_key(master_password, salt)

    payload = json.dumps(EMPTY_VAULT).encode("utf-8")
    ciphertext = encrypt_data(payload, fernet_key)

    with open(VAULT_PATH, "wb") as f:
        f.write(MAGIC)
        f.write(salt)
        f.write(pw_hash.encode("ascii"))  # 64 bytes
        f.write(ciphertext)

    return fernet_key


def verify_and_unlock(master_password: str) -> Optional[bytes]:
    """
    Verify master password against stored hash.
    Returns fernet_key on success, None on failure.
    """
    from encryption import hash_password, derive_key

    if not vault_exists():
        return None

    with open(VAULT_PATH, "rb") as f:
        magic = f.read(4)
        if magic != MAGIC:
            raise ValueError("Invalid vault file format.")
        salt = f.read(SALT_LEN)
        stored_hash = f.read(HASH_LEN).decode("ascii")

    candidate_hash = hash_password(master_password, salt)
    if candidate_hash != stored_hash:
        return None  # wrong password

    return derive_key(master_password, salt)


def load_vault(fernet_key: bytes) -> dict:
    """Decrypt and return vault JSON."""
    from encryption import decrypt_data

    with open(VAULT_PATH, "rb") as f:
        f.read(4)            # magic
        f.read(SALT_LEN)     # salt
        f.read(HASH_LEN)     # pw hash
        ciphertext = f.read()

    payload = decrypt_data(ciphertext, fernet_key)
    return json.loads(payload.decode("utf-8"))


def save_vault(data: dict, fernet_key: bytes):
    """Re-encrypt and write vault to disk."""
    from encryption import encrypt_data

    # Read existing header
    with open(VAULT_PATH, "rb") as f:
        magic = f.read(4)
        salt = f.read(SALT_LEN)
        pw_hash = f.read(HASH_LEN)

    payload = json.dumps(data).encode("utf-8")
    ciphertext = encrypt_data(payload, fernet_key)

    with open(VAULT_PATH, "wb") as f:
        f.write(magic)
        f.write(salt)
        f.write(pw_hash)
        f.write(ciphertext)


def add_encrypted_file(filename: str, file_data: bytes, fernet_key: bytes) -> str:
    """Encrypt a file and store it; return the stored filename."""
    from encryption import encrypt_file_bytes
    import uuid

    ensure_dirs()
    stored_name = str(uuid.uuid4()) + ".enc"
    encrypted = encrypt_file_bytes(file_data, fernet_key)
    dest = FILES_DIR / stored_name
    dest.write_bytes(encrypted)
    return stored_name


def get_encrypted_file(stored_name: str, fernet_key: bytes) -> bytes:
    from encryption import decrypt_file_bytes

    path = FILES_DIR / stored_name
    return decrypt_file_bytes(path.read_bytes(), fernet_key)


def delete_encrypted_file(stored_name: str):
    path = FILES_DIR / stored_name
    if path.exists():
        path.unlink()

def change_master_password(new_password: str, vault_data: dict, old_key: bytes = None):
    """
    Re-derive a new salt + key from new_password, re-encrypt vault JSON
    and all encrypted files, then overwrite vault.dat.
    old_key is required to re-encrypt the file blobs; if omitted, file blobs
    are left as-is (they cannot be opened after the key changes).
    """
    from encryption import generate_salt, hash_password, derive_key, encrypt_data
    from encryption import decrypt_file_bytes, encrypt_file_bytes
    import json

    ensure_dirs()
    new_salt = generate_salt()
    new_hash = hash_password(new_password, new_salt)
    new_key  = derive_key(new_password, new_salt)

    # Re-encrypt the JSON payload
    payload    = json.dumps(vault_data).encode("utf-8")
    ciphertext = encrypt_data(payload, new_key)

    with open(VAULT_PATH, "wb") as f:
        f.write(MAGIC)
        f.write(new_salt)
        f.write(new_hash.encode("ascii"))
        f.write(ciphertext)

    # Re-encrypt all stored file blobs with the new key
    if old_key and FILES_DIR.exists():
        for enc_file in FILES_DIR.glob("*.enc"):
            try:
                raw       = enc_file.read_bytes()
                plaintext = decrypt_file_bytes(raw, old_key)
                enc_file.write_bytes(encrypt_file_bytes(plaintext, new_key))
            except Exception:
                pass  # skip files that can't be decrypted with old key
