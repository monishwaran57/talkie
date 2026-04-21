# app/core/config.py
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
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
