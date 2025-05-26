"""
Database layer for the auth service
"""

from .connection import get_database, init_database, close_database
from .repositories import UserRepository

__all__ = [
    "get_database",
    "init_database", 
    "close_database",
    "UserRepository",
] 