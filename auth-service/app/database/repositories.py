"""
Repository pattern implementation for data access
"""

from datetime import datetime
from typing import Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection

from ..models import UserInDB, UserOut
from ..core.logging import get_logger
from .connection import get_database

logger = get_logger(__name__)


class UserRepository:
    """Repository for user data access operations"""
    
    def __init__(self):
        self._collection: Optional[AsyncIOMotorCollection] = None
    
    async def _get_collection(self) -> AsyncIOMotorCollection:
        """Get the users collection"""
        if self._collection is None:
            db = await get_database()
            self._collection = db.users
        return self._collection
    
    async def create_user(self, user: UserInDB) -> UserOut:
        """
        Create a new user in the database.
        
        Args:
            user: The user data to create
            
        Returns:
            UserOut: The created user data
            
        Raises:
            Exception: If user creation fails
        """
        collection = await self._get_collection()
        
        # Convert user to dict and remove None id
        user_dict = user.dict(exclude={"id"})
        
        try:
            result = await collection.insert_one(user_dict)
            
            # Fetch the created user
            created_user = await collection.find_one({"_id": result.inserted_id})
            if created_user:
                # Convert ObjectId to string and rename _id to id
                created_user["id"] = str(created_user.pop("_id"))
                return UserOut(**created_user)
            else:
                raise Exception("Failed to retrieve created user")
                
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            raise
    
    async def get_user_by_email(self, email: str) -> Optional[UserInDB]:
        """
        Get a user by email address.
        
        Args:
            email: The user's email address
            
        Returns:
            Optional[UserInDB]: The user data if found, None otherwise
        """
        collection = await self._get_collection()
        
        try:
            user_doc = await collection.find_one({"email": email.lower()})
            if user_doc:
                # Convert ObjectId to string and rename _id to id
                user_doc["id"] = str(user_doc.pop("_id"))
                return UserInDB(**user_doc)
            return None
            
        except Exception as e:
            logger.error(f"Failed to get user by email {email}: {e}")
            return None
    
    async def get_user_by_id(self, user_id: str) -> Optional[UserOut]:
        """
        Get a user by ID.
        
        Args:
            user_id: The user's ID
            
        Returns:
            Optional[UserOut]: The user data if found, None otherwise
        """
        collection = await self._get_collection()
        
        try:
            # Convert string ID to ObjectId
            object_id = ObjectId(user_id)
            user_doc = await collection.find_one({"_id": object_id})
            
            if user_doc:
                # Convert ObjectId to string and rename _id to id
                user_doc["id"] = str(user_doc.pop("_id"))
                return UserOut(**user_doc)
            return None
            
        except Exception as e:
            logger.error(f"Failed to get user by ID {user_id}: {e}")
            return None
    
    async def update_last_login(self, user_id: str) -> bool:
        """
        Update the user's last login timestamp.
        
        Args:
            user_id: The user's ID
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        collection = await self._get_collection()
        
        try:
            object_id = ObjectId(user_id)
            result = await collection.update_one(
                {"_id": object_id},
                {"$set": {"last_login": datetime.utcnow()}}
            )
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Failed to update last login for user {user_id}: {e}")
            return False
    
    async def increment_failed_login_attempts(self, email: str) -> bool:
        """
        Increment the failed login attempts counter for a user.
        
        Args:
            email: The user's email address
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        collection = await self._get_collection()
        
        try:
            result = await collection.update_one(
                {"email": email.lower()},
                {"$inc": {"failed_login_attempts": 1}}
            )
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Failed to increment failed login attempts for {email}: {e}")
            return False
    
    async def reset_failed_login_attempts(self, email: str) -> bool:
        """
        Reset the failed login attempts counter for a user.
        
        Args:
            email: The user's email address
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        collection = await self._get_collection()
        
        try:
            result = await collection.update_one(
                {"email": email.lower()},
                {"$set": {"failed_login_attempts": 0, "locked_until": None}}
            )
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Failed to reset failed login attempts for {email}: {e}")
            return False
    
    async def lock_user_account(self, email: str, lock_until: datetime) -> bool:
        """
        Lock a user account until a specific time.
        
        Args:
            email: The user's email address
            lock_until: When the lock should expire
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        collection = await self._get_collection()
        
        try:
            result = await collection.update_one(
                {"email": email.lower()},
                {"$set": {"locked_until": lock_until}}
            )
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Failed to lock user account for {email}: {e}")
            return False 