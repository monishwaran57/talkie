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
async def add_contact(request: Request, contact_email:str, db=Depends(get_mongo_db)):
    user_data = request.state.user
    user_id = user_data["sub"]

    existing_user =  await db.users.find_one({"email": contact_email})
    if not existing_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="contact email not found, Invite him to waranapp")


    new_contact = await db.contacts.insert_one({"contact_user_id": existing_user["cognito_id"],
                                                "user_id": user_id,
                                                "contact_email": contact_email,
                                                "contact_name": existing_user["name"],
                                                "created_at": datetime.now()})

    return {"new_contact_id": str(new_contact.inserted_id),
            "new_contact_name": existing_user["name"]}
