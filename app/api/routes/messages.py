from fastapi import WebSocket, APIRouter, Request, Depends
from datetime import datetime
from app.db.mongo import get_mongo_db
from app.core.config import settings
import jwt
from jwt import ExpiredSignatureError, InvalidTokenError

class ConnectionManager:
    def __init__(self):
        self.active_connections = {}  # user_id -> websocket

    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: str):
        self.active_connections.pop(user_id, None)

    async def send_personal_message(self, user_id: str, message: dict):
        if user_id in self.active_connections:
            print("user id in connection---going to send:", message["sender_id"], message["receiver_id"] )
            await self.active_connections[user_id].send_json(message["message"])
            print("message sent successfully")


websocket_route = APIRouter()
manager = ConnectionManager()

@websocket_route.websocket("/connect")
async def websocket_endpoint(websocket: WebSocket, db=Depends(get_mongo_db)):
    # 1. Extract token from query params
    print("Incoming WebSocket request")

    token = websocket.query_params.get("token")
    print("Token:", token)

    if not token:
        print("No token → closing")
        await websocket.close(code=1008)
        return

    if not token:
        await websocket.close(code=1008)
        return

    try:
        # 2. Decode token
        print(".......truiing to decode")
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )

        print("payload", dict(payload))

        user_id = payload["sub"]

    except ExpiredSignatureError:
        print("Token expired")
        await websocket.close(code=1008)
        return

    except InvalidTokenError as e:
        print("Invalid token:", str(e))
        await websocket.close(code=1008)
        return

    # 3. Accept connection AFTER auth
    await manager.connect(user_id, websocket)

    try:
        while True:
            data = await websocket.receive_json()

            receiver_id = data["receiver_id"]
            message = data["message"]

            # 1. Save to MongoDB
            msg_doc = {
                "sender_id": user_id,
                "receiver_id": receiver_id,
                "message": message,
                "timestamp": datetime.utcnow(),
                "status": "sent"
            }

            print(".......messge doc", msg_doc)
            await db.messages.insert_one(msg_doc)

            # 2. Send to receiver if online
            await manager.send_personal_message(receiver_id, msg_doc)

    except:
        manager.disconnect(user_id)