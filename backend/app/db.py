from motor.motor_asyncio import AsyncIOMotorClient
from .config import settings

client = None
db = None


async def connect_db():
    global client, db
    client = AsyncIOMotorClient(settings.mongo_uri)
    db = client[settings.mongo_db]
    # Ensure indexes
    try:
        await db.users.create_index("email", unique=True)
    except Exception:
        pass


async def close_db():
    if client:
        client.close()
