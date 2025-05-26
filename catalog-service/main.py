from fastapi import FastAPI, HTTPException, Depends, Header, Query, Request
from motor.motor_asyncio import AsyncIOMotorClient
from models import Product, Ingredient
from fastapi.middleware.cors import CORSMiddleware
import os, asyncio
from jose import jwt
from typing import Optional, List
from bson.objectid import ObjectId
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
import json
from decimal import Decimal
import re
import logging
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app with documentation settings
app = FastAPI(
    title="Catalog Service",
    description="Service for managing confectionery products",
    version="1.0.0",
    docs_url=None if os.getenv('ENVIRONMENT') == 'production' else "/docs",
    redoc_url=None if os.getenv('ENVIRONMENT') == 'production' else "/redoc"
)

# Rate limiting configuration
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS configuration with specific origins
ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', 'http://localhost:3000,http://localhost:3001').split(',')
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,  # Cache preflight requests for 1 hour
)

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

# Database configuration with connection pooling and retry logic
MONGO_URL = os.getenv('MONGO', 'mongodb://mongo:27017/confectionery')
MAX_POOL_SIZE = int(os.getenv('MONGO_MAX_POOL_SIZE', '100'))
MIN_POOL_SIZE = int(os.getenv('MONGO_MIN_POOL_SIZE', '10'))
MAX_RETRIES = 3

# Global database variables
db = None
products_collection = None

async def init_db():
    global db, products_collection
    
    async def get_database():
        for attempt in range(MAX_RETRIES):
            try:
                client = AsyncIOMotorClient(
                    MONGO_URL,
                    maxPoolSize=MAX_POOL_SIZE,
                    minPoolSize=MIN_POOL_SIZE,
                    serverSelectionTimeoutMS=5000
                )
                await client.admin.command('ping')
                return client.get_database('confectionery')
            except Exception as e:
                if attempt == MAX_RETRIES - 1:
                    logger.error(f"Failed to connect to database after {MAX_RETRIES} attempts: {e}")
                    raise
                await asyncio.sleep(1)
    
    try:
        db = await get_database()
        products_collection = db.get_collection('products')
        # Create indexes
        await products_collection.create_index([("name", 1)], unique=True)
        await products_collection.create_index([("category", 1)])
        await products_collection.create_index([("tags", 1)])
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

@app.on_event("startup")
async def startup_event():
    await init_db()
    await create_test_data()

@app.on_event("shutdown")
async def shutdown_event():
    if 'client' in globals():
        client.close()
        logger.info("Closed MongoDB connection")

# Security configuration
SECRET = os.getenv('SECRET')
if not SECRET or len(SECRET) < 32:
    logger.error("Insecure or missing SECRET key")
    raise ValueError("SECRET key must be at least 32 characters long")

async def verify_token(authorization: Optional[str] = Header(None)) -> dict:
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail='Authorization required',
            headers={"WWW-Authenticate": "Bearer"}
        )
    try:
        scheme, token = authorization.split()
        if scheme.lower() != 'bearer':
            raise HTTPException(
                status_code=401,
                detail='Invalid authentication scheme',
                headers={"WWW-Authenticate": "Bearer"}
            )
        payload = jwt.decode(token, SECRET, algorithms=['HS256'])
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=401,
                detail='Invalid token type',
                headers={"WWW-Authenticate": "Bearer"}
            )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail='Token has expired',
            headers={"WWW-Authenticate": "Bearer"}
        )
    except jwt.JWTError as e:
        raise HTTPException(
            status_code=401,
            detail=f'Invalid token: {str(e)}',
            headers={"WWW-Authenticate": "Bearer"}
        )
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail=f'Authorization failed: {str(e)}',
            headers={"WWW-Authenticate": "Bearer"}
        )

def parse_object_id(id: str) -> ObjectId:
    """Safely parse string to ObjectId"""
    try:
        return ObjectId(id)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f'Invalid ID format: {str(e)}'
        )

@app.get('/products')
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
    sort_by: Optional[str] = Query(None, regex="^(price|name)$", description="Sort field"),
    sort_order: Optional[str] = Query("asc", regex="^(asc|desc)$", description="Sort order")
):
    """List products with pagination, filtering, and sorting."""
    try:
        logger.info(f"Starting products fetch request with params: skip={skip}, limit={limit}")
        
        # Build query
        query = {"is_available": True}
        if category:
            query["category"] = category
        if tag:
            query["tags"] = tag
        if search:
            query["$or"] = [
                {"name": {"$regex": re.escape(search), "$options": "i"}},
                {"description": {"$regex": re.escape(search), "$options": "i"}}
            ]
        if min_price is not None:
            query["price"] = {"$gte": min_price}
        if max_price is not None:
            query.setdefault("price", {})
            query["price"]["$lte"] = max_price

        # Build sort
        sort_field = sort_by if sort_by else "name"
        sort_direction = -1 if sort_order == "desc" else 1
        
        try:
            # Get total count
            total = await products_collection.count_documents(query)
            logger.info(f"Total products found: {total}")

            if total == 0:
                return JSONResponse(content={
                    "total": 0,
                    "products": [],
                    "page": 1,
                    "pages": 0
                })

            # Get paginated results
            cursor = products_collection.find(query)
            cursor.sort(sort_field, sort_direction)
            cursor.skip(skip).limit(limit)
            products = await cursor.to_list(length=limit)
            
            # Transform ObjectId to string and handle decimal serialization
            transformed_products = []
            for product in products:
                product['id'] = str(product.pop('_id'))
                # Convert Decimal to float for JSON serialization
                product['price'] = float(product['price'])
                for ingredient in product.get('recipe', []):
                    ingredient['quantity'] = float(ingredient['quantity'])
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

@app.get('/products/{product_id}')
@limiter.limit("60/minute")
async def get_product(request: Request, product_id: str):
    """Get a single product by ID."""
    try:
        product = await products_collection.find_one({'_id': parse_object_id(product_id)})
        if not product:
            raise HTTPException(
                status_code=404,
                detail='Product not found'
            )
        
        # Transform ObjectId to string and handle decimal serialization
        product['id'] = str(product.pop('_id'))
        product['price'] = float(product['price'])
        for ingredient in product.get('recipe', []):
            ingredient['quantity'] = float(ingredient['quantity'])
        
        return JSONResponse(content=product)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving product: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving product: {str(e)}"
        )

@app.post('/products')
@limiter.limit("10/minute")
async def create_product(request: Request, product: Product, user: dict = Depends(verify_token)):
    """Create a new product. Only sellers can create products."""
    if user.get('role') != 'seller':
        raise HTTPException(
            status_code=403,
            detail='Only sellers can create products'
        )
    
    try:
        # Convert the product to dict and prepare for MongoDB
        product_dict = product.dict(exclude={'id'})
        
        # Validate unique name
        existing = await products_collection.find_one({'name': product_dict['name']})
        if existing:
            raise HTTPException(
                status_code=409,
                detail='Product with this name already exists'
            )
        
        # Convert Decimal to float for MongoDB
        product_dict['price'] = float(product_dict['price'])
        for ingredient in product_dict.get('recipe', []):
            ingredient['quantity'] = float(ingredient['quantity'])
        
        # Add metadata
        product_dict['created_by'] = user.get('sub')
        product_dict['created_at'] = datetime.utcnow()
        product_dict['updated_at'] = datetime.utcnow()
        
        # Insert into MongoDB
        result = await products_collection.insert_one(product_dict)
        
        # Return the created product
        created_product = await products_collection.find_one({'_id': result.inserted_id})
        created_product['id'] = str(created_product.pop('_id'))
        return JSONResponse(
            status_code=201,
            content=created_product
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating product: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error creating product: {str(e)}"
        )

@app.put('/products/{product_id}')
@limiter.limit("20/minute")
async def update_product(
    request: Request,
    product_id: str,
    product: Product,
    user: dict = Depends(verify_token)
):
    """Update an existing product. Only sellers can update products."""
    if user.get('role') != 'seller':
        raise HTTPException(
            status_code=403,
            detail='Only sellers can update products'
        )
    
    try:
        # Get existing product
        existing = await products_collection.find_one({'_id': parse_object_id(product_id)})
        if not existing:
            raise HTTPException(
                status_code=404,
                detail='Product not found'
            )
        
        # Check ownership
        if existing.get('created_by') != user.get('sub'):
            raise HTTPException(
                status_code=403,
                detail='You can only update your own products'
            )
        
        # Convert the product to dict and prepare for MongoDB
        product_dict = product.dict(exclude={'id'})
        
        # Check name uniqueness if changed
        if product_dict['name'] != existing['name']:
            name_exists = await products_collection.find_one({
                '_id': {'$ne': parse_object_id(product_id)},
                'name': product_dict['name']
            })
            if name_exists:
                raise HTTPException(
                    status_code=409,
                    detail='Product with this name already exists'
                )
        
        # Convert Decimal to float for MongoDB
        product_dict['price'] = float(product_dict['price'])
        for ingredient in product_dict.get('recipe', []):
            ingredient['quantity'] = float(ingredient['quantity'])
        
        # Preserve metadata and update timestamp
        product_dict['created_by'] = existing['created_by']
        product_dict['created_at'] = existing['created_at']
        product_dict['updated_at'] = datetime.utcnow()
        
        # Update in MongoDB
        result = await products_collection.replace_one(
            {'_id': parse_object_id(product_id)},
            product_dict
        )
        
        if result.modified_count == 0:
            raise HTTPException(
                status_code=304,
                detail='Product not modified'
            )
        
        # Return the updated product
        updated_product = await products_collection.find_one({'_id': parse_object_id(product_id)})
        updated_product['id'] = str(updated_product.pop('_id'))
        return JSONResponse(content=updated_product)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating product: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error updating product: {str(e)}"
        )

@app.delete('/products/{product_id}')
@limiter.limit("10/minute")
async def delete_product(
    request: Request,
    product_id: str,
    user: dict = Depends(verify_token)
):
    """Delete a product. Only sellers can delete their own products."""
    if user.get('role') != 'seller':
        raise HTTPException(
            status_code=403,
            detail='Only sellers can delete products'
        )
    
    try:
        # Get existing product
        existing = await products_collection.find_one({'_id': parse_object_id(product_id)})
        if not existing:
            raise HTTPException(
                status_code=404,
                detail='Product not found'
            )
        
        # Check ownership
        if existing.get('created_by') != user.get('sub'):
            raise HTTPException(
                status_code=403,
                detail='You can only delete your own products'
            )
        
        result = await products_collection.delete_one({'_id': parse_object_id(product_id)})
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=404,
                detail='Product not found'
            )
        return JSONResponse(
            content={'message': 'Product deleted successfully'},
            status_code=200
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting product: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting product: {str(e)}"
        )

@app.get('/categories')
@limiter.limit("30/minute")
async def list_categories(request: Request):
    """Get a list of all unique product categories."""
    try:
        categories = await products_collection.distinct('category')
        return JSONResponse(content=sorted(categories))
    except Exception as e:
        logger.error(f"Error retrieving categories: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving categories: {str(e)}"
        )

@app.get('/tags')
@limiter.limit("30/minute")
async def list_tags(request: Request):
    """Get a list of all unique product tags."""
    try:
        tags = await products_collection.distinct('tags')
        return JSONResponse(content=sorted(tags))
    except Exception as e:
        logger.error(f"Error retrieving tags: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving tags: {str(e)}"
        )

async def create_test_data():
    """Insert test data if database is empty"""
    try:
        count = await products_collection.count_documents({})
        if count == 0:
            logger.info("No products found, inserting test products")
            test_products = [
                {
                    "name": "Chocolate Cake",
                    "description": "Rich chocolate cake with ganache",
                    "price": 29.99,
                    "category": "Cakes",
                    "is_available": True,
                    "image_url": "https://example.com/chocolate-cake.jpg",
                    "tags": ["chocolate", "cake", "dessert"],
                    "recipe": [
                        {"ingredient": "flour", "quantity": 2.5, "unit": "cups"},
                        {"ingredient": "cocoa", "quantity": 0.75, "unit": "cups"},
                        {"ingredient": "sugar", "quantity": 2.0, "unit": "cups"}
                    ],
                    "created_by": "system",
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                },
                {
                    "name": "Vanilla Cupcakes",
                    "description": "Classic vanilla cupcakes with buttercream",
                    "price": 19.99,
                    "category": "Cupcakes",
                    "is_available": True,
                    "image_url": "https://example.com/vanilla-cupcakes.jpg",
                    "tags": ["vanilla", "cupcakes", "dessert"],
                    "recipe": [
                        {"ingredient": "flour", "quantity": 1.5, "unit": "cups"},
                        {"ingredient": "vanilla", "quantity": 2.0, "unit": "tsp"},
                        {"ingredient": "sugar", "quantity": 1.0, "unit": "cups"}
                    ],
                    "created_by": "system",
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            ]
            await products_collection.insert_many(test_products)
            logger.info("Test products inserted successfully")
    except Exception as e:
        logger.error(f"Error in create_test_data: {str(e)}")

@app.get("/health")
async def health_check():
    """Check service health"""
    try:
        # Check database connection
        await db.command('ping')
        return JSONResponse(
            content={
                "status": "healthy",
                "database": "connected",
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail="Service unhealthy"
        )
