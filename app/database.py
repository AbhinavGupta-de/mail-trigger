from motor.motor_asyncio import AsyncIOMotorClient
from app.config import get_settings

settings = get_settings()


class Database:
    client: AsyncIOMotorClient = None


db = Database()


async def connect_to_mongo():
    db.client = AsyncIOMotorClient(settings.mongodb_url)
    print(f"Connected to MongoDB at {settings.mongodb_url}")


async def close_mongo_connection():
    if db.client:
        db.client.close()
        print("Closed MongoDB connection")


def get_database():
    return db.client[settings.database_name]
