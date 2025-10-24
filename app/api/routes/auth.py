# app/api/routes/auth.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
from uuid import uuid4
from app.db.session import get_db
from app.core.security import generate_otp, hash_otp, generate_salt

router = APIRouter()

class EmailRequest(BaseModel):
    email: EmailStr

@router.post("/request-email-verification")
async def request_email_verification(payload: EmailRequest, background: BackgroundTasks, db=Depends(get_db)):
    async with db as cursor:
        otp = generate_otp()
        salt = generate_salt()
        otp_hash = hash_otp(otp, salt)
        expires_at = datetime.utcnow() + timedelta(minutes=10)

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


from app.core.security import hash_otp
from datetime import datetime

class VerifyEmailRequest(BaseModel):
    email: EmailStr
    otp: str

@router.post("/verify-email")
async def verify_email(payload: VerifyEmailRequest, db=Depends(get_db)):
    await db.execute(
        """
        SELECT id, otp_hash, salt, expires_at, consumed
        FROM otp_codes
        WHERE email = %s AND purpose = 'email_verification'
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (payload.email,)
    )
    record = await db.fetchone()
    if not record:
        raise HTTPException(status_code=404, detail="OTP not found")

    if record["consumed"]:
        raise HTTPException(status_code=400, detail="OTP already used")

    if record["expires_at"] < datetime.utcnow():
        raise HTTPException(status_code=400, detail="OTP expired")

    otp_hash = hash_otp(payload.otp, record["salt"])
    if otp_hash != record["otp_hash"]:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    await db.execute("UPDATE otp_codes SET consumed = true WHERE id = %s", (record["id"],))
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
    await db.execute("SELECT id FROM users WHERE email = %s", (payload.email,))
    existing = await db.fetchone()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Check verified OTP
    await db.execute("""
        SELECT 1 FROM otp_codes
        WHERE email = %s AND purpose = 'email_verification' AND consumed = true
        ORDER BY created_at DESC LIMIT 1
    """, (payload.email,))
    verified = await db.fetchone()
    if not verified:
        raise HTTPException(status_code=400, detail="Email not verified")

    user_id = str(uuid4())
    hashed_pw = hash_password(payload.password)

    await db.execute(
        """
        INSERT INTO users (id, email, full_name, password_hash, email_verified, created_at, updated_at)
        VALUES (%s, %s, %s, %s, true, NOW(), NOW())
        RETURNING id, email, email_verified
        """,
        (user_id, payload.email, payload.full_name, hashed_pw)
    )
    row = await db.fetchone()

    return SignupResponse(
        id=row["id"],
        email=row["email"],
        email_verified=row["email_verified"]
    )
