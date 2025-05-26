from fastapi import APIRouter, HTTPException, Request, status
from typing import List
from slowapi import Limiter
from slowapi.util import get_remote_address

from ...services.product_service import ProductService

# Initialize router
router = APIRouter(
    prefix="/categories",
    tags=["categories"],
    responses={404: {"description": "Categories not found"}},
)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)

@router.get('', response_model=List[str])
@limiter.limit("30/minute")
async def list_categories(request: Request):
    """
    Get all available product categories.
    
    Returns a list of unique categories from all products in the database.
    """
    try:
        product_service = ProductService()
        categories = await product_service.get_categories()
        return categories
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving categories: {str(e)}"
        ) 