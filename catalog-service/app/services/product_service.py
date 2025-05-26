import logging
from typing import List, Dict, Any, Optional
from bson.objectid import ObjectId
from fastapi import HTTPException, status
from datetime import datetime
import json

from ..models import Product
from ..db import get_products_collection

logger = logging.getLogger(__name__)


def custom_json_encoder(obj):
    """Custom JSON encoder for MongoDB ObjectId and other types"""
    try:
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return obj
    except Exception as e:
        logger.error(f"Error in custom_json_encoder: {str(e)}")
        raise


def parse_object_id(id_str: str) -> ObjectId:
    """Parse string to ObjectId with validation"""
    try:
        return ObjectId(id_str)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid product ID format"
        )


class ProductService:
    """Service class for product operations"""
    
    async def list_products(
        self,
        skip: int = 0,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        sort_criteria: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Get products with filtering and pagination"""
        try:
            collection = await get_products_collection()
            
            # Build query
            query = {}
            
            # Apply filters
            if filters:
                if 'category' in filters:
                    query['category'] = filters['category']
                if 'tags' in filters:
                    query['tags'] = filters['tags']
                if 'search' in filters:
                    search_term = filters['search']
                    query['$or'] = [
                        {'name': {'$regex': search_term, '$options': 'i'}},
                        {'description': {'$regex': search_term, '$options': 'i'}}
                    ]
                if 'min_price' in filters or 'max_price' in filters:
                    price_query = {}
                    if 'min_price' in filters:
                        price_query['$gte'] = filters['min_price']
                    if 'max_price' in filters:
                        price_query['$lte'] = filters['max_price']
                    query['price'] = price_query
            
            # Build sort criteria
            sort_list = []
            if sort_criteria:
                sort_direction = 1 if sort_criteria.get('order', 'asc') == "asc" else -1
                sort_list.append((sort_criteria['field'], sort_direction))
            else:
                sort_list.append(("created_at", -1))  # Default sort by creation date
            
            # Execute query with pagination
            cursor = collection.find(query).sort(sort_list).skip(skip).limit(limit)
            products = await cursor.to_list(length=limit)
            
            # Get total count for pagination
            total_count = await collection.count_documents(query)
            
            # Convert ObjectIds to strings
            products_list = [json.loads(json.dumps(product, default=custom_json_encoder)) for product in products]
            
            return {
                "products": products_list,
                "total": total_count,
                "skip": skip,
                "limit": limit,
                "has_more": skip + limit < total_count
            }
            
        except Exception as e:
            logger.error(f"Error fetching products: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch products"
            )
    
    async def get_product(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Get a product by ID"""
        try:
            collection = await get_products_collection()
            object_id = parse_object_id(product_id)
            
            product = await collection.find_one({"_id": object_id})
            
            if product:
                return json.loads(json.dumps(product, default=custom_json_encoder))
            return None
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error retrieving product {product_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve product"
            )
    
    async def create_product(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new product"""
        try:
            collection = await get_products_collection()
            
            # Add timestamps
            product_data.update({
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            })
            
            # Insert product
            result = await collection.insert_one(product_data)
            
            # Fetch the created product
            created_product = await collection.find_one({"_id": result.inserted_id})
            
            return json.loads(json.dumps(created_product, default=custom_json_encoder))
            
        except Exception as e:
            logger.error(f"Error creating product: {str(e)}")
            if "duplicate key" in str(e).lower():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Product with this name already exists"
                )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create product"
            )
    
    async def update_product(self, product_id: str, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing product"""
        try:
            collection = await get_products_collection()
            object_id = parse_object_id(product_id)
            
            # Add update timestamp
            product_data.update({
                "updated_at": datetime.utcnow()
            })
            
            # Update product
            result = await collection.update_one(
                {"_id": object_id},
                {"$set": product_data}
            )
            
            if result.modified_count == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No changes were made to the product"
                )
            
            # Fetch updated product
            updated_product = await collection.find_one({"_id": object_id})
            
            return json.loads(json.dumps(updated_product, default=custom_json_encoder))
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating product {product_id}: {str(e)}")
            if "duplicate key" in str(e).lower():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Product with this name already exists"
                )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update product"
            )
    
    async def delete_product(self, product_id: str) -> bool:
        """Delete a product"""
        try:
            collection = await get_products_collection()
            object_id = parse_object_id(product_id)
            
            # Delete product
            result = await collection.delete_one({"_id": object_id})
            
            if result.deleted_count == 0:
                return False
            
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting product {product_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete product"
            )
    
    async def get_categories(self) -> List[str]:
        """Get all unique categories"""
        try:
            collection = await get_products_collection()
            categories = await collection.distinct("category")
            return sorted([cat for cat in categories if cat])  # Filter out None/empty values
            
        except Exception as e:
            logger.error(f"Error fetching categories: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch categories"
            )
    
    async def get_tags(self) -> List[str]:
        """Get all unique tags"""
        try:
            collection = await get_products_collection()
            # Get all tags arrays and flatten them
            pipeline = [
                {"$unwind": "$tags"},
                {"$group": {"_id": "$tags"}},
                {"$sort": {"_id": 1}}
            ]
            cursor = collection.aggregate(pipeline)
            tags = [doc["_id"] async for doc in cursor if doc["_id"]]
            return tags
            
        except Exception as e:
            logger.error(f"Error fetching tags: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch tags"
            ) 
    
    async def create_test_data(self):
        """Create test data for development"""
        try:
            collection = await get_products_collection()
            
            # Check if test data already exists
            count = await collection.count_documents({})
            if count > 0:
                logger.info("Test data already exists, skipping creation")
                return
            
            test_products = [
                {
                    "name": "Chocolate Cake",
                    "description": "Rich chocolate cake with ganache frosting",
                    "price": 29.99,
                    "category": "Cakes",
                    "tags": ["chocolate", "cake", "dessert"],
                    "recipe": [
                        {"ingredient": "flour", "quantity": 2.5, "unit": "cups"},
                        {"ingredient": "cocoa", "quantity": 0.75, "unit": "cups"},
                        {"ingredient": "sugar", "quantity": 2.0, "unit": "cups"}
                    ],
                    "is_available": True,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                },
                {
                    "name": "Vanilla Cupcakes",
                    "description": "Light and fluffy vanilla cupcakes with buttercream",
                    "price": 3.99,
                    "category": "Cupcakes",
                    "tags": ["vanilla", "cupcake", "frosting"],
                    "recipe": [
                        {"ingredient": "flour", "quantity": 1.5, "unit": "cups"},
                        {"ingredient": "sugar", "quantity": 1.0, "unit": "cups"},
                        {"ingredient": "butter", "quantity": 0.5, "unit": "cups"}
                    ],
                    "is_available": True,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                },
                {
                    "name": "Strawberry Tart",
                    "description": "Fresh strawberry tart with pastry cream",
                    "price": 24.99,
                    "category": "Tarts",
                    "tags": ["strawberry", "tart", "fresh", "cream"],
                    "recipe": [
                        {"ingredient": "pastry", "quantity": 1, "unit": "shell"},
                        {"ingredient": "strawberries", "quantity": 2, "unit": "cups"},
                        {"ingredient": "cream", "quantity": 1, "unit": "cup"}
                    ],
                    "is_available": True,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            ]
            
            await collection.insert_many(test_products)
            logger.info("Test data created successfully")
            
        except Exception as e:
            logger.error(f"Error creating test data: {str(e)}") 