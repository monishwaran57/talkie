# app/api/routes/auth.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status, Request
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from app.db.session import get_db
from app.core.security import (
    generate_otp, hash_otp, generate_salt,
    verify_password, generate_refresh_token, hash_token,
    create_access_token, create_id_token)
from app.core.config import settings

router = APIRouter()

class EmailRequest(BaseModel):
    email: EmailStr

@router.post("/request-email-verification")
async def request_email_verification(payload: EmailRequest, background: BackgroundTasks, db=Depends(get_db)):
    async with db as cursor:
        otp = generate_otp()
        salt = generate_salt()
        otp_hash = hash_otp(otp, salt)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)

        # Delete any old OTPs
        await cursor.execute(
            "DELETE FROM otp_codes WHERE email = %s AND purpose = 'email_verification'",
            (payload.email,)
        )

        # Insert new OTP
        await cursor.execute(
            """
            INSERT INTO otp_codes (id, email, otp_hash, salt, purpose, expires_at, consumed, created_at)
            VALUES (%s, %s, %s, %s, 'email_verification', %s, false, NOW())
            """,
            (str(uuid4()), payload.email, otp_hash, salt, expires_at)
        )

        background.add_task(print, f"[DEBUG] OTP for {payload.email} is {otp}")

        return {"message": "OTP sent successfully"}


class VerifyEmailRequest(BaseModel):
    email: EmailStr
    otp: str

@router.post("/verify-email")
async def verify_email(payload: VerifyEmailRequest, db=Depends(get_db)):
    async with db as cursor:
        await cursor.execute(
            """
            SELECT id, otp_hash, salt, expires_at, consumed
            FROM otp_codes
            WHERE email = %s AND purpose = 'email_verification'
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (payload.email,)
        )
        record = await cursor.fetchone()
        if not record:
            raise HTTPException(status_code=404, detail="OTP not found")

        if record["consumed"]:
            raise HTTPException(status_code=400, detail="OTP already used")

        if record["expires_at"] < datetime.now(timezone.utc):
            raise HTTPException(status_code=400, detail="OTP expired")

        otp_hash = hash_otp(payload.otp, record["salt"])
        if otp_hash != record["otp_hash"]:
            raise HTTPException(status_code=400, detail="Invalid OTP")

        await cursor.execute("UPDATE otp_codes SET consumed = true WHERE id = %s", (record["id"],))
        return {"message": "Email verified successfully"}



from app.core.security import hash_password

class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None

class SignupResponse(BaseModel):
    id: str
    email: str
    email_verified: bool

@router.post("/signup", response_model=SignupResponse)
async def signup(payload: SignupRequest, db=Depends(get_db)):
    # Check existing user
    async with db as cursor:
        await cursor.execute("SELECT id FROM users WHERE email = %s", (payload.email,))
        existing = await cursor.fetchone()
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")

        # Check verified OTP
        await cursor.execute("""
            SELECT 1 FROM otp_codes
            WHERE email = %s AND purpose = 'email_verification' AND consumed = true
            ORDER BY created_at DESC LIMIT 1
        """, (payload.email,))
        verified = await cursor.fetchone()
        if not verified:
            raise HTTPException(status_code=400, detail="Email not verified")

        user_id = str(uuid4())
        hashed_pw = hash_password(payload.password)

        await cursor.execute(
            """
            INSERT INTO users (id, email, full_name, password_hash, email_verified, created_at, updated_at)
            VALUES (%s, %s, %s, %s, true, NOW(), NOW())
            RETURNING id, email, email_verified
            """,
            (user_id, payload.email, payload.full_name, hashed_pw)
        )
        row = await cursor.fetchone()

        return SignupResponse(
            id=str(row["id"]),
            email=row["email"],
            email_verified=row["email_verified"]
        )


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    access_token: str
    id_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # access token lifetime seconds

@router.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest, request: Request, db = Depends(get_db)):
    # 1) fetch user by email (raw SQL)
    async with db as cursor:
        await cursor.execute("SELECT id, password_hash, full_name FROM users WHERE email = %s", (payload.email,))
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

        user_id = row["id"]
        password_hash = row["password_hash"]
        full_name = row.get("full_name")

        # 2) verify password
        if not password_hash or not verify_password(payload.password, password_hash):
            # consider logging failed attempts separately
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

        # 3) create ID and access tokens (JWT)
        access_token = create_access_token(str(user_id))
        id_token = create_id_token(str(user_id), str(payload.email), full_name)

        # 4) create refresh token (unhashed for client), store hashed in DB
        refresh_token_plain = generate_refresh_token()
        refresh_token_hash = hash_token(refresh_token_plain)

        refresh_id = str(uuid4())
        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        user_agent = request.headers.get("user-agent")
        ip_addr = request.client.host if request.client else None

        insert_q = """
        INSERT INTO refresh_tokens (id, user_id, token_hash, user_agent, ip_addr, expires_at, revoked, created_at, replaced_by)
        VALUES (%s, %s, %s, %s, %s, %s, false, NOW(), NULL)
        """
        await cursor.execute(insert_q, (refresh_id, user_id, refresh_token_hash, user_agent, ip_addr, expires_at))
        # commit is handled by your get_db context manager's commit/rollback logic.
        # If your get_db requires explicit commit use: await db.connection.commit()
        try:
            # If your contextmanager yields cursor, you might need to explicitly commit:
            await cursor.connection.commit()
        except Exception:
            await cursor.connection.rollback()
            raise

        response = {
            "access_token": access_token,
            "id_token": id_token,
            "refresh_token": refresh_token_plain,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES
        }
        return response