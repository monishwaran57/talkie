# app/core/config.py
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    DATABASE_URL: str

    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15 * 60  # 15 minutes in seconds
    ID_TOKEN_EXPIRE_MINUTES: int = 15 * 60  # 15 minutes
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # class Config:
    #     env_file = ".env"

settings = Settings()
