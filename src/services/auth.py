"""Authentication service with secure password hashing and signed token management."""

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
import uuid
import logging
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from cryptography.fernet import Fernet
from src.database.models import UserRecord

logger = logging.getLogger("llm_judge.auth")

# Secret key for token signing - defaults to env var or secure fallback
AUTH_SECRET_KEY = os.environ.get("AUTH_SECRET_KEY", "llm-judge-secret-key-production-38f9a2b7c")
TOKEN_EXPIRATION_SECONDS = 7 * 24 * 3600  # 7 days

# Encryption cipher derivation for sensitive API keys at rest
def _get_fernet() -> Fernet:
    enc_seed = os.environ.get("ENCRYPTION_SECRET_KEY", AUTH_SECRET_KEY)
    key_32 = hashlib.sha256(enc_seed.encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(key_32))


def encrypt_api_key(plain_key: str) -> str:
    """Encrypt plain API key at rest using Fernet (AES-128-CBC + HMAC-SHA256)."""
    if not plain_key or not plain_key.strip():
        return ""
    try:
        cipher = _get_fernet()
        token = cipher.encrypt(plain_key.strip().encode("utf-8")).decode("utf-8")
        return f"enc:{token}"
    except Exception as exc:
        logger.error("Failed to encrypt API key: %s", exc)
        return plain_key


def decrypt_api_key(stored_key: str) -> str:
    """Decrypt stored API key. Falls back gracefully for unencrypted legacy keys."""
    if not stored_key:
        return ""
    if stored_key.startswith("enc:"):
        try:
            cipher = _get_fernet()
            return cipher.decrypt(stored_key[4:].encode("utf-8")).decode("utf-8")
        except Exception as exc:
            logger.warning("Decryption failed; returning raw string: %s", exc)
            return stored_key
    return stored_key


class AuthService:
    """Handles password hashing, token generation, user verification, and session authentication."""

    @staticmethod
    def hash_password(password: str, salt: Optional[str] = None) -> str:
        """Hash a password using PBKDF2-HMAC-SHA256 with 100,000 iterations."""
        if not salt:
            salt = secrets.token_hex(16)
        pwd_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            100_000
        ).hex()
        return f"{salt}${pwd_hash}"

    @classmethod
    def verify_password(cls, plain_password: str, stored_hash: str) -> bool:
        """Verify plain password against stored salt$hash."""
        try:
            salt, _ = stored_hash.split("$", 1)
            expected = cls.hash_password(plain_password, salt)
            return hmac.compare_digest(expected, stored_hash)
        except Exception:
            return False

    @staticmethod
    def create_access_token(user_id: str, username: str) -> str:
        """Create a tamper-proof HMAC-SHA256 signed bearer token."""
        payload = {
            "sub": user_id,
            "username": username,
            "exp": int(time.time()) + TOKEN_EXPIRATION_SECONDS,
            "nonce": secrets.token_hex(8)
        }
        payload_bytes = json.dumps(payload).encode("utf-8")
        payload_b64 = base64.urlsafe_b64encode(payload_bytes).decode("utf-8")

        signature = hmac.new(
            AUTH_SECRET_KEY.encode("utf-8"),
            payload_b64.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

        return f"{payload_b64}.{signature}"

    @staticmethod
    def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
        """Verify token signature and return payload if valid and not expired."""
        try:
            parts = token.split(".", 1)
            if len(parts) != 2:
                return None
            payload_b64, signature = parts

            expected_sig = hmac.new(
                AUTH_SECRET_KEY.encode("utf-8"),
                payload_b64.encode("utf-8"),
                hashlib.sha256
            ).hexdigest()

            if not hmac.compare_digest(signature, expected_sig):
                return None

            payload_bytes = base64.urlsafe_b64decode(payload_b64.encode("utf-8"))
            payload = json.loads(payload_bytes.decode("utf-8"))

            # Check expiration
            if payload.get("exp", 0) < time.time():
                return None

            return payload
        except Exception:
            return None

    @classmethod
    def register_user(
        cls,
        db: Session,
        username: str,
        email: str,
        password: str
    ) -> Dict[str, Any]:
        """Register a new user."""
        clean_user = username.strip()
        clean_email = email.strip().lower()

        if len(clean_user) < 3:
            raise ValueError("Username must be at least 3 characters long.")
        if len(password) < 6:
            raise ValueError("Password must be at least 6 characters long.")
        if "@" not in clean_email or "." not in clean_email:
            raise ValueError("A valid email address is required.")

        # Check existing
        if db.query(UserRecord).filter(UserRecord.username == clean_user).first():
            raise ValueError(f"Username '{clean_user}' is already registered.")
        if db.query(UserRecord).filter(UserRecord.email == clean_email).first():
            raise ValueError(f"Email '{clean_email}' is already registered.")

        user_id = f"usr-{uuid.uuid4().hex[:10]}"
        pwd_hash = cls.hash_password(password)

        new_user = UserRecord(
            id=user_id,
            username=clean_user,
            email=clean_email,
            password_hash=pwd_hash
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        token = cls.create_access_token(user_id=new_user.id, username=new_user.username)
        return {
            "user": {
                "id": new_user.id,
                "username": new_user.username,
                "email": new_user.email,
                "created_at": new_user.created_at.isoformat() if new_user.created_at else None
            },
            "token": token
        }

    @classmethod
    def authenticate_user(
        cls,
        db: Session,
        username_or_email: str,
        password: str
    ) -> Dict[str, Any]:
        """Authenticate user and return profile with access token."""
        query_val = username_or_email.strip()

        user = (
            db.query(UserRecord)
            .filter((UserRecord.username == query_val) | (UserRecord.email == query_val.lower()))
            .first()
        )
        if not user or not cls.verify_password(password, user.password_hash):
            raise ValueError("Invalid username/email or password.")

        token = cls.create_access_token(user_id=user.id, username=user.username)
        return {
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "created_at": user.created_at.isoformat() if user.created_at else None
            },
            "token": token
        }

    @classmethod
    def get_current_user_from_token(cls, db: Session, token: str) -> Optional[UserRecord]:
        """Extract and verify user from bearer token."""
        payload = cls.decode_access_token(token)
        if not payload:
            return None
        user_id = payload.get("sub")
        return db.query(UserRecord).filter(UserRecord.id == user_id).first()
