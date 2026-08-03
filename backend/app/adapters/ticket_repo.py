from bson.objectid import ObjectId
from datetime import datetime


async def create_ticket(db, ticket_doc: dict):
    ticket_doc.setdefault("status", "open")
    ticket_doc.setdefault("created_at", datetime.utcnow())
    res = await db.tickets.insert_one(ticket_doc)
    ticket = await db.tickets.find_one({"_id": res.inserted_id})
    ticket["_id"] = str(ticket["_id"])
    return ticket


async def get_ticket_by_id(db, id: str):
    try:
        oid = ObjectId(id)
    except Exception:
        return None
    ticket = await db.tickets.find_one({"_id": oid})
    if ticket:
        ticket["_id"] = str(ticket["_id"])
    return ticket


async def list_tickets_for_user(db, user_id: str):
    cursor = db.tickets.find({"user_id": user_id}).sort("created_at", -1)
    items = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        items.append(doc)
    return items
