import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def make_admin():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["support_copilot"]

    result = await db.users.update_one(
        {"email": "sujankm201@gmail.com"},
        {"$set": {"is_admin": True}}
    )

    print("Matched:", result.matched_count)
    print("Modified:", result.modified_count)

    client.close()

asyncio.run(make_admin())