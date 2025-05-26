from fastapi import FastAPI, HTTPException, Depends, Header, Query
from motor.motor_asyncio import AsyncIOMotorClient
from models import Product, Ingredient
from fastapi.middleware.cors import CORSMiddleware
import os
from jose import jwt
from typing import Optional, List
from bson.objectid import ObjectId
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
import json
from decimal import Decimal
import re
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Catalog Service",
    description="Service for managing confectionery products",
    version="1.0.0"
)

# Simplified CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connect to MongoDB with explicit database name
MONGO_URL = os.getenv('MONGO', 'mongodb://mongo:27017/confectionery')
client = AsyncIOMotorClient(MONGO_URL)
db = client.get_database('confectionery')
products_collection = db.get_collection('products')
SECRET = os.getenv('SECRET', 'your_jwt_secret')

def parse_object_id(id: str) -> ObjectId:
    """Safely parse string to ObjectId"""
    try:
        return ObjectId(id)
    except:
        raise HTTPException(400, 'Invalid ID format')

async def verify_token(authorization: Optional[str] = Header(None)) -> dict:
    if not authorization:
        raise HTTPException(401, 'Authorization required')
    try:
        token = authorization.split(' ')[1]
        payload = jwt.decode(token, SECRET, algorithms=['HS256'])
        return payload
    except jwt.JWTError as e:
        raise HTTPException(401, f'Invalid token: {str(e)}')
    except Exception as e:
        raise HTTPException(401, f'Authorization failed: {str(e)}')

@app.options("/products")
async def products_options():
    """Handle OPTIONS preflight request"""
    return JSONResponse(
        content={},
        headers={
            "Access-Control-Allow-Origin": "http://localhost:3001",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Max-Age": "86400",
        }
    )

@app.get('/products')
async def list_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    authorization: Optional[str] = Header(None)
):
    """List products with pagination."""
    try:
        logger.info("Starting products fetch request")
        
        # Basic query for available products
        query = {}  # Remove the is_available filter temporarily for testing
        
        try:
            # Test database connection
            await products_collection.find_one()
            logger.info("Database connection successful")
        except Exception as db_err:
            logger.error(f"Database connection error: {str(db_err)}")
            raise HTTPException(
                status_code=500,
                detail=f"Database connection error: {str(db_err)}"
            )

        try:
            # Get total count
            total = await products_collection.count_documents(query)
            logger.info(f"Total products found: {total}")

            if total == 0:
                logger.info("No products found in database")
                return JSONResponse(content={
                    "total": 0,
                    "products": [],
                    "page": 1,
                    "pages": 0
                })

            # Get paginated results
            cursor = products_collection.find(query).skip(skip).limit(limit)
            products = await cursor.to_list(length=limit)
            
            # Transform ObjectId to string
            transformed_products = []
            for product in products:
                product['id'] = str(product.pop('_id'))
                transformed_products.append(product)
            
            logger.info(f"Successfully fetched {len(transformed_products)} products")
            
            return JSONResponse(content={
                "total": total,
                "products": transformed_products,
                "page": skip // limit + 1,
                "pages": (total + limit - 1) // limit
            })

        except Exception as query_err:
            logger.error(f"Error querying products: {str(query_err)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error querying products: {str(query_err)}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in list_products: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )

@app.get('/products/{product_id}', response_model=Product)
async def get_product(product_id: str):
    """
    Get a single product by ID.
    """
    try:
        product = await products_collection.find_one({'_id': parse_object_id(product_id)})
        if not product:
            raise HTTPException(404, 'Product not found')
        
        product['id'] = str(product.pop('_id'))
        return JSONResponse(content=product)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Error retrieving product: {str(e)}")

@app.post('/products', response_model=Product)
async def create_product(product: Product, user: dict = Depends(verify_token)):
    """
    Create a new product. Only sellers can create products.
    """
    if user.get('role') != 'seller':
        raise HTTPException(403, 'Only sellers can create products')
    
    try:
        # Convert the product to dict and prepare for MongoDB
        product_dict = product.dict(exclude={'id'})
        
        # Convert Decimal to float for MongoDB
        product_dict['price'] = float(product_dict['price'])
        for ingredient in product_dict.get('recipe', []):
            ingredient['quantity'] = float(ingredient['quantity'])
        
        # Insert into MongoDB
        result = await products_collection.insert_one(product_dict)
        
        # Return the created product
        created_product = await products_collection.find_one({'_id': result.inserted_id})
        created_product['id'] = str(created_product.pop('_id'))
        return JSONResponse(content=created_product)
    except Exception as e:
        raise HTTPException(500, f"Error creating product: {str(e)}")

@app.put('/products/{product_id}', response_model=Product)
async def update_product(product_id: str, product: Product, user: dict = Depends(verify_token)):
    """
    Update an existing product. Only sellers can update products.
    """
    if user.get('role') != 'seller':
        raise HTTPException(403, 'Only sellers can update products')
    
    try:
        # Convert the product to dict and prepare for MongoDB
        product_dict = product.dict(exclude={'id'})
        
        # Convert Decimal to float for MongoDB
        product_dict['price'] = float(product_dict['price'])
        for ingredient in product_dict.get('recipe', []):
            ingredient['quantity'] = float(ingredient['quantity'])
        
        # Update in MongoDB
        result = await products_collection.update_one(
            {'_id': parse_object_id(product_id)},
            {'$set': product_dict}
        )
        
        if result.modified_count == 0:
            raise HTTPException(404, 'Product not found')
        
        # Return the updated product
        updated_product = await products_collection.find_one({'_id': parse_object_id(product_id)})
        updated_product['id'] = str(updated_product.pop('_id'))
        return JSONResponse(content=updated_product)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Error updating product: {str(e)}")

@app.delete('/products/{product_id}')
async def delete_product(product_id: str, user: dict = Depends(verify_token)):
    """
    Delete a product. Only sellers can delete products.
    """
    if user.get('role') != 'seller':
        raise HTTPException(403, 'Only sellers can delete products')
    
    try:
        result = await products_collection.delete_one({'_id': parse_object_id(product_id)})
        if result.deleted_count == 0:
            raise HTTPException(404, 'Product not found')
        return JSONResponse(content={'message': 'Product deleted successfully'})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Error deleting product: {str(e)}")

@app.get('/categories')
async def list_categories():
    """
    Get a list of all unique product categories.
    """
    try:
        categories = await products_collection.distinct('category')
        return JSONResponse(content=categories)
    except Exception as e:
        raise HTTPException(500, f"Error retrieving categories: {str(e)}")

@app.get('/tags')
async def list_tags():
    """
    Get a list of all unique product tags.
    """
    try:
        tags = await products_collection.distinct('tags')
        return JSONResponse(content=tags)
    except Exception as e:
        raise HTTPException(500, f"Error retrieving tags: {str(e)}")

@app.on_event("startup")
async def startup_event():
    """Insert test data if database is empty"""
    try:
        count = await products_collection.count_documents({})
        if count == 0:
            logger.info("No products found, inserting test product")
            test_product = {
                "name": "Test Cake",
                "description": "A delicious test cake",
                "price": 9.99,
                "category": "Cakes",
                "is_available": True,
                "image_url": "https://example.com/cake.jpg",
                "tags": ["test", "cake"],
                "recipe": [
                    {"ingredient": "flour", "quantity": 2.0, "unit": "cups"},
                    {"ingredient": "sugar", "quantity": 1.5, "unit": "cups"}
                ]
            }
            await products_collection.insert_one(test_product)
            logger.info("Test product inserted successfully")
    except Exception as e:
        logger.error(f"Error in startup event: {str(e)}")
