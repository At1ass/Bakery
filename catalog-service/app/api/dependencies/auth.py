from fastapi import Depends
from typing import Dict, Any

from ...core.security import verify_token


async def get_current_user(token_data: Dict[str, Any] = Depends(verify_token)) -> Dict[str, Any]:
    """
    Dependency to get the current authenticated user from JWT token.
    
    Args:
        token_data: The decoded JWT token data
        
    Returns:
        Dictionary containing user information
    """
    return token_data 