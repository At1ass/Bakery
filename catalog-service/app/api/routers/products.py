from fastapi import APIRouter, HTTPException, Depends, Query, Request, status
from typing import Optional, List, Dict, Any
from slowapi import Limiter
from slowapi.util import get_remote_address
from pydantic import BaseModel
import logging

from ...models.product import Product
from ...services.product_service import ProductService
from ...core.security import verify_token
from ...core.config import settings

# Response models for better API documentation
class ProductListResponse(BaseModel):
    products: List[Dict[str, Any]]
    total: int
    skip: int
    limit: int
    has_more: bool

class ProductResponse(BaseModel):
    product: Dict[str, Any]

class ProductCreateResponse(BaseModel):
    message: str
    product: Dict[str, Any]

class ProductUpdateResponse(BaseModel):
    message: str
    product: Dict[str, Any]

class ProductDeleteResponse(BaseModel):
    message: str

# Initialize router
router = APIRouter(
    prefix="/products",
    tags=["products"],
    responses={404: {"description": "Product not found"}},
)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)

logger = logging.getLogger(__name__)

@router.get('', response_model=ProductListResponse)
@limiter.limit("30/minute")
async def list_products(
    request: Request,  # Required for rate limiting
    skip: int = Query(0, ge=0, description="Number of products to skip"),
    limit: int = Query(10, ge=1, le=100, description="Number of products to return"),
    category: Optional[str] = Query(None, description="Filter by category"),
    tag: Optional[str] = Query(None, description="Filter by tag"),
    search: Optional[str] = Query(None, min_length=1, description="Search in name and description"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price"),
    max_price: Optional[float] = Query(None, gt=0, description="Maximum price"),
    sort_by: Optional[str] = Query(None, pattern="^(price|name)$", description="Sort field"),
    sort_order: Optional[str] = Query("asc", pattern="^(asc|desc)$", description="Sort order")
):
    """
    Retrieve a list of products with optional filtering, searching, and sorting.
    
    - **skip**: Number of products to skip (for pagination)
    - **limit**: Maximum number of products to return (1-100)
    - **category**: Filter products by category
    - **tag**: Filter products by tag
    - **search**: Search in product name and description
    - **min_price**: Minimum price filter
    - **max_price**: Maximum price filter
    - **sort_by**: Sort by 'price' or 'name'
    - **sort_order**: Sort order 'asc' or 'desc'
    """
    try:
        product_service = ProductService()
        
        # Build filter criteria
        filters = {}
        if category:
            filters['category'] = category
        if tag:
            filters['tags'] = tag
        if search:
            filters['search'] = search
        if min_price is not None:
            filters['min_price'] = min_price
        if max_price is not None:
            filters['max_price'] = max_price
            
        # Build sort criteria
        sort_criteria = None
        if sort_by:
            sort_criteria = {
                'field': sort_by,
                'order': sort_order
            }
        
        result = await product_service.list_products(
            skip=skip,
            limit=limit,
            filters=filters,
            sort_criteria=sort_criteria
        )
        
        return ProductListResponse(**result)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving products: {str(e)}"
        )

@router.post('/', status_code=status.HTTP_201_CREATED, response_model=ProductCreateResponse)
@limiter.limit("10/minute")
async def create_product(
    request: Request, 
    product: Product, 
    user: Dict[str, Any] = Depends(verify_token)
):
    """
    Create a new product.
    
    Requires authentication and appropriate permissions.
    Only users with 'admin', 'manager', or 'seller' roles can create products.
    """
    try:
        # Check if user has permission to create products
        user_role = user.get('role', '').lower()
        
        if user_role not in ['admin', 'manager', 'seller']:
            logger.warning(f"User {user.get('user_id')} with role '{user_role}' attempted to create product")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions to create products. Required roles: admin, manager, seller. Your role: {user_role}"
            )
        
        product_service = ProductService()
        created_product = await product_service.create_product(product.dict())
        
        return ProductCreateResponse(
            message="Product created successfully",
            product=created_product
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating product: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating product: {str(e)}"
        )

@router.put('/{product_id}', response_model=ProductUpdateResponse)
@limiter.limit("20/minute")
async def update_product(
    request: Request,
    product_id: str,
    product: Product,
    user: Dict[str, Any] = Depends(verify_token)
):
    """
    Update an existing product.
    
    Requires authentication and appropriate permissions.
    Only users with 'admin', 'manager', or 'seller' roles can update products.
    """
    try:
        # Check if user has permission to update products
        user_role = user.get('role', '').lower()
        if user_role not in ['admin', 'manager', 'seller']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to update products"
            )
        
        product_service = ProductService()
        updated_product = await product_service.update_product(product_id, product.dict())
        
        if not updated_product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
            
        return ProductUpdateResponse(
            message="Product updated successfully",
            product=updated_product
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating product: {str(e)}"
        )

@router.delete('/{product_id}', response_model=ProductDeleteResponse)
@limiter.limit("10/minute")
async def delete_product(
    request: Request,
    product_id: str,
    user: Dict[str, Any] = Depends(verify_token)
):
    """
    Delete a product.
    
    Requires authentication and appropriate permissions.
    Only users with 'admin', 'manager', or 'seller' roles can delete products.
    """
    try:
        # Check if user has permission to delete products
        user_role = user.get('role', '').lower()
        if user_role not in ['admin', 'manager', 'seller']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to delete products"
            )
        
        product_service = ProductService()
        success = await product_service.delete_product(product_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
            
        return ProductDeleteResponse(
            message="Product deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting product: {str(e)}"
        )

# This route must come LAST to avoid conflicts with specific routes like /debug/test
@router.get('/{product_id}', response_model=ProductResponse)
@limiter.limit("60/minute")
async def get_product(request: Request, product_id: str):
    """
    Get a specific product by ID.
    
    - **product_id**: The ID of the product to retrieve
    """
    try:
        product_service = ProductService()
        product = await product_service.get_product(product_id)
        
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
            
        return ProductResponse(product=product)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving product: {str(e)}"
        ) 