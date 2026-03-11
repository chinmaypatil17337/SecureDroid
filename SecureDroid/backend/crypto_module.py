"""
SecureDroid - Cryptography Module
Implements AES-256 encryption and SHA-256 hashing for secure report storage.
"""

import os
import json
import base64
import hashlib
import secrets
from datetime import datetime, timezone

try:
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import pad, unpad
    AES_AVAILABLE = True
except ImportError:
    AES_AVAILABLE = False

try:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import padding as sym_padding
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False


# ─────────────────────────────────────────────────────────────
# AES-256-CBC Encryption / Decryption
# ─────────────────────────────────────────────────────────────

class AESCipher:
    """
    AES-256-CBC cipher with PKCS7 padding.
    Key is derived via SHA-256 so any passphrase length works.
    """

    BLOCK_SIZE = 16  # AES block size in bytes

    def __init__(self, key: str):
        # Derive a 32-byte key from the passphrase using SHA-256
        self.key = hashlib.sha256(key.encode("utf-8")).digest()

    # ── Encrypt ──────────────────────────────────────────────

    def encrypt(self, plaintext: str) -> dict:
        """
        Encrypt plaintext and return a dict with:
          - iv        : base64-encoded initialisation vector
          - ciphertext: base64-encoded ciphertext
          - timestamp : UTC ISO-8601 timestamp
        """
        iv = secrets.token_bytes(self.BLOCK_SIZE)
        data = plaintext.encode("utf-8")

        if AES_AVAILABLE:
            cipher = AES.new(self.key, AES.MODE_CBC, iv)
            ct = cipher.encrypt(pad(data, self.BLOCK_SIZE))
        elif CRYPTO_AVAILABLE:
            padder = sym_padding.PKCS7(128).padder()
            padded = padder.update(data) + padder.finalize()
            cipher = Cipher(algorithms.AES(self.key), modes.CBC(iv),
                            backend=default_backend())
            enc = cipher.encryptor()
            ct = enc.update(padded) + enc.finalize()
        else:
            raise RuntimeError("No AES library available (install pycryptodome or cryptography).")

        return {
            "iv": base64.b64encode(iv).decode("utf-8"),
            "ciphertext": base64.b64encode(ct).decode("utf-8"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    # ── Decrypt ──────────────────────────────────────────────

    def decrypt(self, payload: dict) -> str:
        """
        Decrypt a payload produced by encrypt().
        """
        iv = base64.b64decode(payload["iv"])
        ct = base64.b64decode(payload["ciphertext"])

        if AES_AVAILABLE:
            cipher = AES.new(self.key, AES.MODE_CBC, iv)
            plaintext = unpad(cipher.decrypt(ct), self.BLOCK_SIZE)
        elif CRYPTO_AVAILABLE:
            cipher = Cipher(algorithms.AES(self.key), modes.CBC(iv),
                            backend=default_backend())
            dec = cipher.decryptor()
            padded = dec.update(ct) + dec.finalize()
            unpadder = sym_padding.PKCS7(128).unpadder()
            plaintext = unpadder.update(padded) + unpadder.finalize()
        else:
            raise RuntimeError("No AES library available.")

        return plaintext.decode("utf-8")


# ─────────────────────────────────────────────────────────────
# SHA-256 Helpers
# ─────────────────────────────────────────────────────────────

def sha256_hash(text: str) -> str:
    """Return the hex-encoded SHA-256 digest of text."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def verify_integrity(text: str, expected_hash: str) -> bool:
    """Check that the SHA-256 digest of text matches expected_hash."""
    return sha256_hash(text) == expected_hash


# ─────────────────────────────────────────────────────────────
# Report Builder
# ─────────────────────────────────────────────────────────────

_DEFAULT_KEY = os.environ.get("SECUREDROID_AES_KEY", "SecureDroid@AES256Key!")


def encrypt_scan_report(report: dict, key: str = _DEFAULT_KEY) -> dict:
    """
    Encrypt a scan report dict. Returns an envelope with:
      - encrypted_data: AES-encrypted JSON
      - package_hash  : SHA-256 of the package name (integrity anchor)
    """
    cipher = AESCipher(key)
    plaintext = json.dumps(report, ensure_ascii=False)
    encrypted = cipher.encrypt(plaintext)

    pkg = report.get("package_name", "unknown")
    return {
        "encrypted_data": encrypted,
        "package_hash": sha256_hash(pkg),
        "schema_version": "1.0",
    }


def decrypt_scan_report(envelope: dict, key: str = _DEFAULT_KEY) -> dict:
    """Decrypt an envelope produced by encrypt_scan_report()."""
    cipher = AESCipher(key)
    plaintext = cipher.decrypt(envelope["encrypted_data"])
    return json.loads(plaintext)
