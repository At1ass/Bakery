import aiohttp
import logging
from typing import Dict, Any, Optional
from fastapi import HTTPException, status

from ..core.config import settings

logger = logging.getLogger(__name__)


class ExternalServiceError(Exception):
    """Custom exception for external service errors"""
    pass


class AuthService:
    """Service for communicating with the authentication service"""
    
    def __init__(self):
        self.base_url = settings.auth_service_url
    
    async def get_user_details(self, user_id: str, token: str) -> Dict[str, Any]:
        """Get user details from auth service"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {token}"}
                url = f"{self.base_url}/users/{user_id}"
                
                async with session.get(url, headers=headers, timeout=10) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 404:
                        raise HTTPException(
                            status_code=status.HTTP_404_NOT_FOUND,
                            detail="User not found"
                        )
                    else:
                        logger.error(f"Auth service error: {response.status}")
                        raise ExternalServiceError(f"Auth service returned {response.status}")
                        
        except aiohttp.ClientError as e:
            logger.error(f"Failed to connect to auth service: {str(e)}")
            raise ExternalServiceError("Auth service unavailable")
        except Exception as e:
            logger.error(f"Unexpected error calling auth service: {str(e)}")
            raise ExternalServiceError("Auth service error")


class CatalogService:
    """Service for communicating with the catalog service"""
    
    def __init__(self):
        self.base_url = settings.catalog_service_url
    
    async def get_product_details(self, product_id: str) -> Dict[str, Any]:
        """Get product details from catalog service"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/products/{product_id}"
                
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('product', {})
                    elif response.status == 404:
                        raise HTTPException(
                            status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Product {product_id} not found"
                        )
                    else:
                        logger.error(f"Catalog service error: {response.status}")
                        raise ExternalServiceError(f"Catalog service returned {response.status}")
                        
        except aiohttp.ClientError as e:
            logger.error(f"Failed to connect to catalog service: {str(e)}")
            raise ExternalServiceError("Catalog service unavailable")
        except Exception as e:
            logger.error(f"Unexpected error calling catalog service: {str(e)}")
            raise ExternalServiceError("Catalog service error")
    
    async def validate_products(self, product_ids: list) -> Dict[str, Dict[str, Any]]:
        """Validate multiple products and return their details"""
        products = {}
        
        for product_id in product_ids:
            try:
                product = await self.get_product_details(product_id)
                products[product_id] = product
            except HTTPException as e:
                if e.status_code == 404:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Product {product_id} not found in catalog"
                    )
                raise
        
        return products


# Service instances
auth_service = AuthService()
catalog_service = CatalogService() 