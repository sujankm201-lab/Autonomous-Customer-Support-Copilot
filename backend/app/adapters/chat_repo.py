from bson.objectid import ObjectId
from datetime import datetime


async def create_chat(db, chat_doc: dict):
    chat_doc.setdefault("created_at", datetime.utcnow())
    chat_doc.setdefault("updated_at", datetime.utcnow())
    chat_doc.setdefault("messages", [])

    res = await db.chats.insert_one(chat_doc)

    chat = await db.chats.find_one({"_id": res.inserted_id})

    if chat:
        chat["_id"] = str(chat["_id"])

    return chat


async def get_chat_by_id(db, id: str):
    try:
        oid = ObjectId(id)
    except Exception:
        return None

    chat = await db.chats.find_one({"_id": oid})

    print("CHAT FROM DB:", chat)

    if chat:
        chat["_id"] = str(chat["_id"])

    return chat


async def get_chat_by_ticket_id(db, ticket_id: str):
    chat = await db.chats.find_one({"ticket_id": ticket_id})

    if chat:
        chat["_id"] = str(chat["_id"])

    return chat


async def list_chats_for_user(db, user_id: str):
    cursor = db.chats.find(
        {"user_id": user_id}
    ).sort("updated_at", -1)

    items = []

    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        items.append(doc)

    return items


async def add_message_to_chat(db, chat_id: str, message: dict):
    try:
        oid = ObjectId(chat_id)
    except Exception:
        return None

    chat = await db.chats.find_one({"_id": oid})

    if not chat:
        return None

    message["_id"] = str(ObjectId())
    message["ticket_id"] = chat.get("ticket_id")
    message["created_at"] = datetime.utcnow()

    await db.chats.update_one(
        {"_id": oid},
        {
            "$push": {
                "messages": message
            }
        }
    )

    await db.chats.update_one(
        {"_id": oid},
        {
            "$set": {
                "updated_at": datetime.utcnow()
            }
        }
    )

    updated_chat = await db.chats.find_one({"_id": oid})

    if updated_chat:
        updated_chat["_id"] = str(updated_chat["_id"])

    return updated_chat


async def delete_chat(db, chat_id: str):
    try:
        oid = ObjectId(chat_id)
    except Exception:
        return False

    result = await db.chats.delete_one({"_id": oid})

    return result.deleted_count > 0
