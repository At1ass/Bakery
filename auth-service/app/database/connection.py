"""
Database connection management
"""

import asyncio
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from ..core.config import settings
from ..core.logging import get_logger

logger = get_logger(__name__)

# Global database client and database instances
_client: Optional[AsyncIOMotorClient] = None
_database: Optional[AsyncIOMotorDatabase] = None


async def get_database_client() -> AsyncIOMotorClient:
    """
    Create and return a database client with proper connection settings.
    
    Returns:
        AsyncIOMotorClient: The MongoDB client
    """
    client = AsyncIOMotorClient(
        settings.mongo_uri,
        maxPoolSize=settings.mongo_max_pool_size,
        minPoolSize=settings.mongo_min_pool_size,
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=5000,
        socketTimeoutMS=10000,
        retryWrites=True,
        w="majority"
    )
    return client


async def init_database() -> None:
    """
    Initialize the database connection with retry logic.
    
    Raises:
        Exception: If connection fails after all retries
    """
    global _client, _database
    
    for attempt in range(settings.mongo_max_retries):
        try:
            _client = await get_database_client()
            
            # Verify connection is working
            await _client.admin.command('ping')
            
            # Get database instance
            _database = _client[settings.mongo_db_name]
            
            # Setup collections and indexes
            await _setup_indexes()
            
            logger.info("Successfully connected to MongoDB and initialized collections")
            return
            
        except Exception as e:
            if attempt < settings.mongo_max_retries - 1:
                logger.warning(
                    f"Database connection attempt {attempt + 1} failed: {str(e)}. "
                    f"Retrying in {settings.mongo_retry_delay}s..."
                )
                await asyncio.sleep(settings.mongo_retry_delay)
            else:
                logger.error(f"Failed to connect to database after {settings.mongo_max_retries} attempts: {str(e)}")
                raise


async def _setup_indexes() -> None:
    """
    Setup database indexes for optimal performance.
    """
    if _database is None:
        raise RuntimeError("Database not initialized")
    
    users_collection = _database.users
    
    # Create email index if it doesn't exist
    existing_indexes = await users_collection.index_information()
    
    if 'email_1' not in existing_indexes:
        await users_collection.create_index([("email", 1)], unique=True)
        logger.info("Created email index on users collection")
    
    # Create compound index for email and active status
    if 'email_1_is_active_1' not in existing_indexes:
        await users_collection.create_index([("email", 1), ("is_active", 1)])
        logger.info("Created compound index on users collection")


async def get_database() -> AsyncIOMotorDatabase:
    """
    Get the database instance.
    
    Returns:
        AsyncIOMotorDatabase: The database instance
        
    Raises:
        RuntimeError: If database is not initialized
    """
    if _database is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    return _database


async def close_database() -> None:
    """
    Close the database connection.
    """
    global _client, _database
    
    if _client:
        _client.close()
        _client = None
        _database = None
        logger.info("Closed MongoDB connection") 