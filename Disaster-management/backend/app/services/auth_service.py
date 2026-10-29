"""
Authentication and Token Management Service for DisasterShield AI
Uses hashlib.pbkdf2_hmac for secure password hashing and HMAC-SHA256 signed bearer tokens.
Zero external fragile binary dependencies required.
"""

import os
import hmac
import hashlib
import base64
import json
import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any

# Secret key for signing bearer tokens
SECRET_KEY = os.environ.get("DISASTER_SHIELD_SECRET", "disaster-shield-secure-key-2026-sdma-western-ghats")
TOKEN_EXPIRY_HOURS = 48


def hash_password(password: str, salt: Optional[str] = None) -> str:
    """Hashes a password with PBKDF2-HMAC-SHA256 and salt"""
    if not salt:
        salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        100000
    )
    return f"{salt}${key.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies plain password against stored hash"""
    try:
        salt, expected_hex = hashed_password.split("$", 1)
        actual_key = hashlib.pbkdf2_hmac(
            "sha256",
            plain_password.encode("utf-8"),
            salt.encode("utf-8"),
            100000
        )
        return hmac.compare_digest(actual_key.hex(), expected_hex)
    except Exception:
        return False


def create_access_token(user_id: int, email: str, role: str, full_name: str) -> str:
    """Generates an HMAC-SHA256 signed JWT-style token"""
    expires = (datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIRY_HOURS)).isoformat()
    payload = {
        "user_id": user_id,
        "email": email,
        "role": role,
        "full_name": full_name,
        "exp": expires,
        "nonce": secrets.token_hex(8)
    }
    header = {"alg": "HS256", "typ": "JWT"}
    
    header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    
    message = f"{header_b64}.{payload_b64}".encode()
    signature = hmac.new(SECRET_KEY.encode(), message, hashlib.sha256).digest()
    sig_b64 = base64.urlsafe_b64encode(signature).decode().rstrip("=")
    
    return f"{header_b64}.{payload_b64}.{sig_b64}"


def verify_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Validates and unpacks a signed token"""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        header_b64, payload_b64, sig_b64 = parts
        
        # Verify signature
        message = f"{header_b64}.{payload_b64}".encode()
        expected_sig = hmac.new(SECRET_KEY.encode(), message, hashlib.sha256).digest()
        
        # Add padding back if necessary
        sig_padding = "=" * (-len(sig_b64) % 4)
        actual_sig = base64.urlsafe_b64decode(sig_b64 + sig_padding)
        
        if not hmac.compare_digest(expected_sig, actual_sig):
            return None
        
        payload_padding = "=" * (-len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64 + payload_padding).decode())
        
        # Check expiry
        exp_time = datetime.fromisoformat(payload["exp"])
        if datetime.now(timezone.utc) > exp_time:
            return None
            
        return payload
    except Exception:
        return None
