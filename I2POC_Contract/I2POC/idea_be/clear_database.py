#!/usr/bin/env python3
"""
Script to clear all data from the MongoDB database
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure


async def clear_database():
    """Clear all documents from the ideas collection"""
    try:
        # Get MongoDB connection details from environment variables
        mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
        database_name = os.getenv("MONGODB_DATABASE", "contract_generation")
        collection_name = os.getenv("MONGODB_COLLECTION", "contracts")
        
        print(f"🔗 Connecting to MongoDB: {mongodb_url}")
        print(f"📁 Database: {database_name}")
        print(f"📄 Collection: {collection_name}")
        
        # Connect to MongoDB
        client = AsyncIOMotorClient(mongodb_url)
        db = client[database_name]
        collection = db[collection_name]
        
        # Test connection
        await client.admin.command('ping')
        print("✅ Connected to MongoDB successfully")
        
        # Count documents before deletion
        count_before = await collection.count_documents({})
        print(f"📊 Documents before deletion: {count_before}")
        
        if count_before == 0:
            print("ℹ️  Database is already empty")
            return
        
        # Delete all documents
        result = await collection.delete_many({})
        print(f"🗑️  Deleted {result.deleted_count} documents")
        
        # Count documents after deletion
        count_after = await collection.count_documents({})
        print(f"📊 Documents after deletion: {count_after}")
        
        if count_after == 0:
            print("✅ Database cleared successfully!")
        else:
            print("❌ Failed to clear all documents")
        
        # Close connection
        client.close()
        print("🔌 MongoDB connection closed")
        
    except ConnectionFailure:
        print("❌ Failed to connect to MongoDB")
        print("💡 Make sure MongoDB is running on localhost:27017")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    print("🚀 Starting database cleanup...")
    print("⚠️  WARNING: This will delete ALL data from the database!")
    print("   This action cannot be undone!")
    
    # Ask for confirmation
    response = input("❓ Are you sure you want to continue? (yes/no): ")
    
    if response.lower() in ['yes', 'y']:
        asyncio.run(clear_database())
    else:
        print("❌ Operation cancelled")
