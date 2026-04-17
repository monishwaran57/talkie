# app/core/config.py
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    DATABASE_URL: str
    SQL_DB_NAME: str
    SQL_DB_USER: str
    SQL_DB_PASSWORD: str

    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 300 * 60  # 15 minutes in seconds
    ID_TOKEN_EXPIRE_MINUTES: int = 15 * 60  # 15 minutes
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    ADMIN_EMAIL:str
    AWS_ACCESS_KEY: str
    AWS_SECRET_KEY: str

    MONGO_URI: str
    MONGO_DB_NAME: str

    COGNITO_REGION: str
    COGNITO_USER_POOL_ID: str
    COGNITO_APP_CLIENT_ID: str

    # class Config:
    #     env_file = ".env"

settings = Settings()
