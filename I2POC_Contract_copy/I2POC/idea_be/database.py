from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure
import os
from datetime import datetime

class Database:
    client: AsyncIOMotorClient = None
    db = None

    @classmethod
    async def connect_db(cls):
        """Connect to MongoDB"""
        mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
        try:
            cls.client = AsyncIOMotorClient(mongodb_url)
            cls.db = cls.client[os.getenv("MONGODB_DATABASE", "i2poc")]
            # Test connection
            await cls.client.admin.command('ping')
            print("✅ Connected to MongoDB")
        except ConnectionFailure:
            print("❌ Failed to connect to MongoDB")
            raise

    @classmethod
    async def close_db(cls):
        """Close MongoDB connection"""
        if cls.client:
            cls.client.close()
            print("✅ MongoDB connection closed")

    @classmethod
    def get_collection(cls, collection_name: str):
        """Get collection instance"""
        return cls.db[collection_name]

# Global collection reference
ideas_collection = None

async def get_ideas_collection():
    """Dependency injection for FastAPI"""
    global ideas_collection
    if ideas_collection is None:
        await Database.connect_db()
        ideas_collection = Database.get_collection(os.getenv("MONGODB_COLLECTION", "ideas"))
    return ideas_collection
