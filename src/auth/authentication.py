"""
Authentication Engine for Panama PortOps-AI v2.0
Handles cryptographic password hashing (PBKDF2-HMAC-SHA256), RFC 6238 TOTP MFA,
and secure tamper-proof signed session tokens.
Author: Desarrollado v1.0 Miguel Benítez - GNU GPL-3.0
"""

import os
import time
import json
import hmac
import struct
import base64
import hashlib
import secrets
from typing import Dict, Any, Optional, Tuple


class AuthenticationEngine:
    """Enterprise authentication with zero mocks, secure hashing and MFA."""

    SALT_BYTES = 32
    ITERATIONS = 120_000
    SECRET_KEY = os.getenv("PORTOPS_AUTH_SECRET", "panama_portops_jwt_secret_key_v2_2026_miguel_benitez")

    @classmethod
    def hash_password(cls, password: str, salt: Optional[str] = None) -> Tuple[str, str]:
        """Hashes password with PBKDF2-HMAC-SHA256 and unique salt."""
        if salt is None:
            salt_bytes = secrets.token_bytes(cls.SALT_BYTES)
            salt_hex = salt_bytes.hex()
        else:
            salt_bytes = bytes.fromhex(salt)
            salt_hex = salt

        key = hashlib.pbkdf2_hmac(
            hash_name="sha256",
            password=password.encode("utf-8"),
            salt=salt_bytes,
            iterations=cls.ITERATIONS
        )
        return key.hex(), salt_hex

    @classmethod
    def verify_password(cls, password: str, password_hash: str, salt: str) -> bool:
        """Verifies password in constant time to prevent timing attacks."""
        computed_hash, _ = cls.hash_password(password, salt)
        return hmac.compare_digest(computed_hash, password_hash)

    # --- TOTP MFA Implementation (RFC 6238) ---
    @classmethod
    def generate_mfa_secret(cls) -> str:
        """Generates a base32 encoded random 160-bit secret key for TOTP."""
        random_bytes = secrets.token_bytes(20)
        return base64.b32encode(random_bytes).decode("utf-8").replace("=", "")

    @classmethod
    def generate_totp_code(cls, secret_base32: str, time_step: int = 30) -> str:
        """Generates the current 6-digit TOTP code for a secret."""
        # Pad secret if needed
        pad_len = (8 - len(secret_base32) % 8) % 8
        key = base64.b32decode(secret_base32 + "=" * pad_len, casefold=True)
        t = int(time.time() // time_step)
        msg = struct.pack(">Q", t)
        h = hmac.new(key, msg, hashlib.sha1).digest()
        offset = h[-1] & 0x0F
        code = (struct.unpack(">I", h[offset:offset + 4])[0] & 0x7FFFFFFF) % 1_000_000
        return f"{code:06d}"

    @classmethod
    def verify_totp(cls, secret_base32: str, code_to_check: str, window: int = 1) -> bool:
        """Verifies TOTP with drift tolerance window (+- 30s)."""
        clean_code = str(code_to_check).strip()
        current_time = int(time.time())
        pad_len = (8 - len(secret_base32) % 8) % 8
        try:
            key = base64.b32decode(secret_base32 + "=" * pad_len, casefold=True)
        except Exception:
            return False

        for w in range(-window, window + 1):
            t = int((current_time + w * 30) // 30)
            msg = struct.pack(">Q", t)
            h = hmac.new(key, msg, hashlib.sha1).digest()
            offset = h[-1] & 0x0F
            code = (struct.unpack(">I", h[offset:offset + 4])[0] & 0x7FFFFFFF) % 1_000_000
            if hmac.compare_digest(f"{code:06d}", clean_code):
                return True
        return False

    # --- Tamper-proof Signed Token Implementation ---
    @classmethod
    def create_token(cls, payload: Dict[str, Any], expires_in_seconds: int = 3600) -> str:
        """Generates a cryptographically signed URL-safe session token."""
        header = {"alg": "HS256", "typ": "JWT"}
        full_payload = {
            **payload,
            "jti": secrets.token_hex(16),
            "iat": int(time.time()),
            "exp": int(time.time() + expires_in_seconds)
        }
        h_str = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
        p_str = base64.urlsafe_b64encode(json.dumps(full_payload).encode()).decode().rstrip("=")
        to_sign = f"{h_str}.{p_str}".encode("utf-8")
        sig = hmac.new(cls.SECRET_KEY.encode("utf-8"), to_sign, hashlib.sha256).digest()
        sig_str = base64.urlsafe_b64encode(sig).decode().rstrip("=")
        return f"{h_str}.{p_str}.{sig_str}"

    @classmethod
    def verify_token(cls, token: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """Verifies signature and expiration of a signed token."""
        try:
            parts = token.strip().split(".")
            if len(parts) != 3:
                return False, None, "Formato de token inválido."

            h_str, p_str, sig_str = parts
            to_sign = f"{h_str}.{p_str}".encode("utf-8")
            expected_sig = hmac.new(cls.SECRET_KEY.encode("utf-8"), to_sign, hashlib.sha256).digest()
            expected_sig_str = base64.urlsafe_b64encode(expected_sig).decode().rstrip("=")

            if not hmac.compare_digest(sig_str, expected_sig_str):
                return False, None, "Firma criptográfica del token inválida o adulterada."

            # Decode payload
            pad_len = (4 - len(p_str) % 4) % 4
            payload = json.loads(base64.urlsafe_b64decode(p_str + "=" * pad_len).decode("utf-8"))

            if time.time() > payload.get("exp", 0):
                return False, None, "El token ha expirado. Por favor inicie sesión nuevamente."

            return True, payload, None
        except Exception as e:
            return False, None, f"Error validando token: {str(e)}"
