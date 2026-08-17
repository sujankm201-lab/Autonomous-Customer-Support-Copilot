import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def reset_password():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["support_copilot"]

    new_password = "Sujan@12345"

    result = await db.users.update_one(
        {"email": "sujankm201@gmail.com"},
        {"$set": {"password": pwd_context.hash(new_password)}}
    )

    print("Matched:", result.matched_count)
    print("Modified:", result.modified_count)

    client.close()


asyncio.run(reset_password())