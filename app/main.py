# app/main.py
from fastapi import FastAPI, Depends
from app.api.routes import auth, contacts
from app.api.routes.contacts import contacts_router
from app.api.routes.websocket_connection import websocket_route
from app.api.routes.messages import message_route
from contextlib import asynccontextmanager
from motor.motor_asyncio import AsyncIOMotorClient
from app.db.mongo import mongo
from app.core.config import settings
from app.core.security import verify_and_decode_access_token


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 🔹 Startup
    mongo.client = AsyncIOMotorClient(settings.MONGO_URI)
    mongo.db = mongo.client[settings.MONGO_DB_NAME]

    print("✅ MongoDB connected")

    yield

    # 🔹 Shutdown
    mongo.client.close()
    print("❌ MongoDB disconnected")

app = FastAPI(title="Auth API", lifespan=lifespan)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(contacts_router, prefix="/contacts", tags=["contacts"], dependencies=[Depends(verify_and_decode_access_token)])
app.include_router(websocket_route, prefix="/ws", tags=["websocket"])
app.include_router(message_route, prefix="/msg", tags=["Message"], dependencies=[Depends(verify_and_decode_access_token)])


import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.main:app", reload=True)