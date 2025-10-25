from passlib.context import CryptContext
import hashlib, os, random
import secrets
import time
import jwt
from datetime import datetime, timedelta
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# OTP helpers
def generate_otp() -> str:
    """Generate a 6-digit numeric OTP"""
    return f"{random.randint(100000, 999999)}"

def hash_otp(otp: str, salt: str) -> str:
    """Hash OTP with salt using SHA256"""
    return hashlib.sha256(f"{otp}{salt}".encode()).hexdigest()

def generate_salt() -> str:
    return os.urandom(16).hex()

def generate_refresh_token(nbytes: int = 48) -> str:
    # URL-safe token for client (store only hashed version on server)
    return secrets.token_urlsafe(nbytes)

def hash_token(token: str) -> str:
    # SHA256 hexdigest for storing in DB
    return hashlib.sha256(token.encode()).hexdigest()

# JWT creation
def create_jwt(payload: dict, expires_in_seconds: int, token_type: str = "access") -> str:
    now = int(time.time())
    claims = {
        "iat": now,
        "exp": now + expires_in_seconds,
        "typ": token_type,
        **payload
    }
    token = jwt.encode(claims, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    # pyjwt returns str in modern versions
    return token

def create_access_token(user_id: str) -> str:
    payload = {"sub": user_id}
    return create_jwt(payload, settings.ACCESS_TOKEN_EXPIRE_MINUTES, token_type="access")

def create_id_token(user_id: str, email: str, full_name: str | None = None) -> str:
    payload = {"sub": user_id, "email": email}
    if full_name:
        payload["name"] = full_name
    return create_jwt(payload, settings.ID_TOKEN_EXPIRE_MINUTES, token_type="id")
