"""
AuthUtils — JWT 令牌生成与密码哈希
"""
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from loguru import logger

from app.core.config import get_settings

settings = get_settings()


def hash_password(password: str) -> str:
    """使用 SHA-256 + salt 哈希密码"""
    salt = secrets.token_hex(16)
    hashed = hashlib.sha256(f"{salt}:{password}".encode()).hexdigest()
    return f"{salt}${hashed}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    if "$" not in hashed_password:
        return False
    salt, expected = hashed_password.split("$", 1)
    computed = hashlib.sha256(f"{salt}:{plain_password}".encode()).hexdigest()
    return hmac.compare_digest(computed, expected)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None
