from datetime import datetime
from fastapi import APIRouter, Request, HTTPException, Depends, status
from app.db.mongo import get_mongo_db
from app.db.session import get_db

contacts_router = APIRouter()

@contacts_router.get("/get_contacts")
async def get_contacts(request: Request, db=Depends(get_mongo_db)):
    user_data = request.state.user

    user_id = user_data["sub"]

    print("userIidiid.....................", user_id)
    contacts_cursor = db.contacts.find({"user_id": user_id})

    contacts = [{**contact, "_id": str(contact["_id"])} async for contact in contacts_cursor]

    return contacts

@contacts_router.get("/add_contact/{contact_email}")
async def add_contact(request: Request, contact_email:str, db=Depends(get_mongo_db), auth_db=Depends(get_db)):
    user_data = request.state.user
    user_id = user_data["sub"]

    async with auth_db as cursor:
        await cursor.execute("SELECT id, full_name FROM users WHERE email = %s", (contact_email,))
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="contact email not found, Invite him to waranapp")


    new_contact = await db.contacts.insert_one({"contact_user_id": str(row["id"]),
                                                "user_id": user_id,
                                                "contact_email": contact_email,
                                                "contact_name": row["full_name"],
                                                "created_at": datetime.now()})

    return {"new_contact_id": str(new_contact.inserted_id),
            "new_contact_name": row["full_name"]}
