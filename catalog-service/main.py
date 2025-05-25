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

app = FastAPI(
    title="Catalog Service",
    description="Service for managing confectionery products",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connect to MongoDB with explicit database name
MONGO_URL = os.getenv('MONGO', 'mongodb://mongo:27017/confectionery')
client = AsyncIOMotorClient(MONGO_URL)
db = client.get_database('confectionery').get_collection('products')
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

@app.get('/products', response_model=List[Product])
async def list_products(
    skip: int = Query(0, ge=0, description="Number of products to skip"),
    limit: int = Query(10, ge=1, le=100, description="Number of products to return"),
    search: Optional[str] = Query(None, description="Search in name and description"),
    category: Optional[str] = Query(None, description="Filter by category"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price"),
    max_price: Optional[float] = Query(None, gt=0, description="Maximum price"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags"),
    available_only: bool = Query(True, description="Show only available products")
):
    """
    List products with pagination and filtering options.
    """
    query = {}
    
    # Build query filters
    if search:
        regex = re.compile(f".*{re.escape(search)}.*", re.IGNORECASE)
        query["$or"] = [
            {"name": {"$regex": regex}},
            {"description": {"$regex": regex}}
        ]
    
    if category:
        query["category"] = category
    
    if min_price is not None or max_price is not None:
        query["price"] = {}
        if min_price is not None:
            query["price"]["$gte"] = min_price
        if max_price is not None:
            query["price"]["$lte"] = max_price
    
    if tags:
        query["tags"] = {"$all": tags}
    
    if available_only:
        query["is_available"] = True

    try:
        # Get total count for pagination
        total = await db.count_documents(query)
        
        # Get paginated results
        cursor = db.find(query).skip(skip).limit(limit)
        products = await cursor.to_list(length=limit)
        
        # Transform products
        for product in products:
            product['id'] = str(product.pop('_id'))
        
        return JSONResponse(content={
            "total": total,
            "skip": skip,
            "limit": limit,
            "products": products
        })
    except Exception as e:
        raise HTTPException(500, f"Error retrieving products: {str(e)}")

@app.get('/products/{product_id}', response_model=Product)
async def get_product(product_id: str):
    """
    Get a single product by ID.
    """
    try:
        product = await db.find_one({'_id': parse_object_id(product_id)})
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
        result = await db.insert_one(product_dict)
        
        # Return the created product
        created_product = await db.find_one({'_id': result.inserted_id})
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
        result = await db.update_one(
            {'_id': parse_object_id(product_id)},
            {'$set': product_dict}
        )
        
        if result.modified_count == 0:
            raise HTTPException(404, 'Product not found')
        
        # Return the updated product
        updated_product = await db.find_one({'_id': parse_object_id(product_id)})
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
        result = await db.delete_one({'_id': parse_object_id(product_id)})
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
        categories = await db.distinct('category')
        return JSONResponse(content=categories)
    except Exception as e:
        raise HTTPException(500, f"Error retrieving categories: {str(e)}")

@app.get('/tags')
async def list_tags():
    """
    Get a list of all unique product tags.
    """
    try:
        tags = await db.distinct('tags')
        return JSONResponse(content=tags)
    except Exception as e:
        raise HTTPException(500, f"Error retrieving tags: {str(e)}")
