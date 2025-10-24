from passlib.context import CryptContext
import hashlib, os, random

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
