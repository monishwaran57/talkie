from datetime import datetime
from fastapi import APIRouter, Request, HTTPException, Depends, status
from app.db.mongo import get_mongo_db
from app.db.session import get_db

convos_router = APIRouter()

@convos_router.get("/get_convos")
async def get_convos(request: Request, db=Depends(get_mongo_db)):
    user_data = request.state.user

    user_id = user_data["sub"]

    print("userIidiid", user_id)
    convos_cursor = db.convos.find({"sender_id": user_id})

    convos = [{**convo, "_id": str(convo["_id"])} async for convo in convos_cursor]

    return convos

@convos_router.get("/add_convo/{contact_email}")
async def add_convo(request: Request, contact_email:str, db=Depends(get_mongo_db), auth_db=Depends(get_db)):
    user_data = request.state.user
    user_id = user_data["sub"]

    async with auth_db as cursor:
        await cursor.execute("SELECT id, full_name FROM users WHERE email = %s", (contact_email,))
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="contact email not found, Invite him to waranapp")

        await cursor.execute("SELECT email, full_name FROM users WHERE id = %s", (user_id,))
        current_user = await cursor.fetchone()

        print(".......row, ", row)


    new_convo = await db.convos.insert_many([{"receiver_id": str(row["id"]),
                                                "sender_id": user_id,
                                                "contact_email": contact_email,
                                                "contact_name": row["full_name"],
                                                "created_at": datetime.now()},
                                             {"receiver_id":user_id,
                                                "sender_id": str(row["id"]),
                                                "contact_email": current_user['email'],
                                                "contact_name": current_user["full_name"],
                                                "created_at": datetime.now()}])

    return {"new_convo_id": str(new_convo.inserted_id),
            "new_convo_name": row["full_name"]}
