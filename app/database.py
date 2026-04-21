from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import IndexModel, ASCENDING
from app.config import settings

client: AsyncIOMotorClient = None


def get_database():
    return client[settings.mongo_db_name]


async def connect_db():
    global client
    client = AsyncIOMotorClient(settings.mongo_uri)

    db = get_database()
    await db["metadata"].create_indexes([
        IndexModel([("url", ASCENDING)], unique=True)
    ])


async def close_db():
    global client
    if client:
        client.close()
