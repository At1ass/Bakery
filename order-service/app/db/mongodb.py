import asyncio
import logging
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from typing import Optional

from ..core.config import settings

logger = logging.getLogger(__name__)

# Global database variables
_client: Optional[AsyncIOMotorClient] = None
_database: Optional[AsyncIOMotorDatabase] = None


async def get_database_client() -> AsyncIOMotorClient:
    """Create and return a database client with proper connection settings."""
    client = AsyncIOMotorClient(
        settings.mongo_url,
        maxPoolSize=settings.mongo_max_pool_size,
        minPoolSize=settings.mongo_min_pool_size,
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=5000,
        socketTimeoutMS=10000,
        retryWrites=True,
        w="majority"
    )
    return client


async def init_db() -> None:
    """Initialize the database connection with retry logic."""
    global _client, _database
    
    max_retries = 5
    retry_delay = 1  # seconds
    
    for attempt in range(max_retries):
        try:
            _client = await get_database_client()
            # Verify connection is working
            await _client.admin.command('ping')
            _database = _client[settings.database_name]
            
            # Setup collections and indexes
            orders_collection = _database.get_collection('orders')
            
            # Check if orders collection exists
            collections = await _database.list_collection_names()
            if "orders" not in collections:
                logger.info("Initializing orders collection with indexes")
                # Create the collection by inserting and removing a dummy document
                await orders_collection.insert_one({"_temp": True})
                await orders_collection.delete_one({"_temp": True})
                
            # Create indexes
            existing_indexes = await orders_collection.index_information()
            
            indexes_created = []
            if 'user_id_1' not in existing_indexes:
                await orders_collection.create_index([("user_id", 1)])
                indexes_created.append("user_id")
                
            if 'status_1' not in existing_indexes:
                await orders_collection.create_index([("status", 1)])
                indexes_created.append("status")
                
            if 'created_at_-1' not in existing_indexes:
                await orders_collection.create_index([("created_at", -1)])
                indexes_created.append("created_at")
            
            if indexes_created:
                logger.info(f"Created indexes: {', '.join(indexes_created)}")
            
            logger.info("MongoDB connection established")
            return
            
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"Database connection attempt {attempt + 1} failed: {str(e)}. Retrying in {retry_delay}s...")
                await asyncio.sleep(retry_delay)
            else:
                logger.error(f"Failed to connect to database after {max_retries} attempts: {str(e)}")
                raise


async def get_database() -> AsyncIOMotorDatabase:
    """Get the database instance."""
    if _database is None:
        await init_db()
    return _database


async def get_orders_collection() -> AsyncIOMotorCollection:
    """Get the orders collection."""
    db = await get_database()
    return db.get_collection('orders')


async def close_db_connection() -> None:
    """Close the database connection."""
    global _client
    if _client:
        _client.close()
        _client = None
        logger.info("Database connection closed") 