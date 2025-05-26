from fastapi import APIRouter, HTTPException, Request, status
from typing import List
from slowapi import Limiter
from slowapi.util import get_remote_address

from ...services.product_service import ProductService

# Initialize router
router = APIRouter(
    prefix="/tags",
    tags=["tags"],
    responses={404: {"description": "Tags not found"}},
)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)

@router.get('', response_model=List[str])
@limiter.limit("30/minute")
async def list_tags(request: Request):
    """
    Get all available product tags.
    
    Returns a list of unique tags from all products in the database.
    """
    try:
        product_service = ProductService()
        tags = await product_service.get_tags()
        return tags
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving tags: {str(e)}"
        ) 