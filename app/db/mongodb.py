from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure
from fastapi import HTTPException, status
import logging

from app.config import settings

logger = logging.getLogger(__name__)

class MongoDB:
    client: AsyncIOMotorClient = None
    db = None

db = MongoDB()

async def connect_to_mongodb():
    """Connect to MongoDB database."""
    logger.info("Connecting to MongoDB...")
    db.client = AsyncIOMotorClient(settings.MONGODB_URI)
    db.db = db.client[settings.MONGODB_DB_NAME]

    # Test connection
    try:
        await db.client.admin.command("ismaster")
        logger.info("Connected to MongoDB")
    except ConnectionFailure:
        logger.error("MongoDB connection failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not connect to MongoDB",
        )

async def close_mongodb_connection():
    """Close MongoDB connection."""
    logger.info("Closing MongoDB connection...")
    if db.client:
        db.client.close()
        logger.info("MongoDB connection closed")

def get_database():
    """Get MongoDB database instance."""
    return db.db
