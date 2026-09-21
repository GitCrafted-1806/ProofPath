from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import bcrypt
import jwt
from app.core.config import settings


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against stored bcrypt hash."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8")
        )
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """Generate bcrypt hash for a plaintext password."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except (jwt.PyJWTError, Exception):
        return None


import base64
import hashlib
import os


def _derive_key(salt: bytes) -> bytes:
    """Derive a 32-byte key from JWT_SECRET using PBKDF2."""
    return hashlib.pbkdf2_hmac("sha256", settings.JWT_SECRET.encode("utf-8"), salt, 10000, 32)


def encrypt_token(plain_token: str) -> str:
    """Encrypt a sensitive token at rest using server secret without external dependencies."""
    if not plain_token:
        return ""
    salt = os.urandom(16)
    key = _derive_key(salt)
    data = plain_token.encode("utf-8")
    keystream = hashlib.sha256(key + salt).digest()
    while len(keystream) < len(data):
        keystream += hashlib.sha256(key + keystream).digest()
    encrypted = bytes(b ^ k for b, k in zip(data, keystream))
    return base64.urlsafe_b64encode(salt + encrypted).decode("utf-8")


def decrypt_token(encrypted_token: str) -> str:
    """Decrypt a sensitive token encrypted at rest."""
    if not encrypted_token:
        return ""
    try:
        raw = base64.urlsafe_b64decode(encrypted_token.encode("utf-8"))
        if len(raw) <= 16:
            return ""
        salt = raw[:16]
        encrypted = raw[16:]
        key = _derive_key(salt)
        keystream = hashlib.sha256(key + salt).digest()
        while len(keystream) < len(encrypted):
            keystream += hashlib.sha256(key + keystream).digest()
        decrypted = bytes(b ^ k for b, k in zip(encrypted, keystream))
        return decrypted.decode("utf-8")
    except Exception:
        return ""
