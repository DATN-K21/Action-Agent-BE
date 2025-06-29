import secrets
from datetime import datetime, timedelta
from typing import Any

import jwt
from cryptography.fernet import Fernet
from passlib.context import CryptContext

from app.core.settings import env_settings


class SecurityManager:
    def __init__(self):
        # Password hashing context
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        # JWT algorithm
        self.jwt_algorithm = "HS256"
        # Fernet encryption instance
        self._key = (
            env_settings.MODEL_PROVIDER_ENCRYPTION_KEY.encode()
            if env_settings.MODEL_PROVIDER_ENCRYPTION_KEY
            else Fernet.generate_key()
        )
        self._fernet = Fernet(self._key)

    def create_access_token(self, subject: str | Any, expires_delta: timedelta) -> str:
        """Create a JWT access token"""
        expire = datetime.utcnow() + expires_delta
        to_encode = {"exp": expire, "sub": str(subject)}
        encoded_jwt = jwt.encode(
            to_encode, env_settings.SECRET_KEY, algorithm=self.jwt_algorithm
        )
        return encoded_jwt

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password"""
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """Get hashed password"""
        return self.pwd_context.hash(password)

    def generate_apikey(self) -> str:
        """Generate an API key"""
        return secrets.token_urlsafe(32)

    def generate_short_apikey(self, key: str) -> str:
        """Generate a shortened version of the API key"""
        return f"{key[:4]}...{key[-4:]}"

    def encrypt_api_key(self, data: str) -> str:
        """Encrypt the API key"""
        if not data:
            return data
        return self._fernet.encrypt(data.encode()).decode()

    def decrypt_api_key(self, encrypted_data: str) -> str:
        """Decrypt the API key"""
        if not encrypted_data:
            return encrypted_data
        try:
            return self._fernet.decrypt(encrypted_data.encode()).decode()
        except Exception as e:
            raise ValueError("Decryption failed, invalid API key token") from e


# Initialize the SecurityManager instance
security_manager = SecurityManager()

# Expose commonly used methods for convenience
create_access_token = security_manager.create_access_token
verify_password = security_manager.verify_password
get_password_hash = security_manager.get_password_hash
generate_apikey = security_manager.generate_apikey
generate_short_apikey = security_manager.generate_short_apikey
