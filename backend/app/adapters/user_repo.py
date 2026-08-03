from bson.objectid import ObjectId


async def get_user_by_email(db, email: str):
    user = await db.users.find_one({"email": email})
    if user:
        user["_id"] = str(user["_id"])
    return user


async def get_user_by_id(db, id: str):
    try:
        oid = ObjectId(id)
    except Exception:
        return None
    user = await db.users.find_one({"_id": oid})
    if user:
        user["_id"] = str(user["_id"])
    return user


async def create_user(db, user_doc: dict):
    res = await db.users.insert_one(user_doc)
    user = await db.users.find_one({"_id": res.inserted_id})
    user["_id"] = str(user["_id"])
    return user
