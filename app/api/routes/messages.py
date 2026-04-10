from fastapi import APIRouter, Request, Depends, HTTPException
from app.db.mongo import get_mongo_db

message_route = APIRouter()

@message_route.get("/get_messages/{contact_user_id}")
async def get_messages(request: Request, contact_user_id: str, db=Depends(get_mongo_db)):
    user_data = request.state.user

    user_id = user_data["sub"]

    messages = await db.messages.find({"$or":
                                           [
                                               {"sender_id": user_id,
                                                "receiver_id": contact_user_id},
                                               {"receiver_id": user_id,
                                                "sender_id": contact_user_id}
                                           ]}, {"_id": 0}).to_list(length=25)

    return messages
