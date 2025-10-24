# app/main.py
from fastapi import FastAPI
from app.api.routes import auth

app = FastAPI(title="Auth API")

app.include_router(auth.router, prefix="/auth", tags=["auth"])


import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.main:app", reload=True)