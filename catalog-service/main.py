from fastapi import FastAPI, HTTPException, Depends, Header, Query, Request, status
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field, ConfigDict
from bson.objectid import ObjectId
from typing import Optional, List, Dict, Any, Annotated, Union
from models import Product, Ingredient
import os, asyncio
import json
import re
import logging
import traceback
from jose import jwt, JWTError
from decimal import Decimal
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def log_separator(message=""):
    logger.info("="*50)
    if message:
        logger.info(f"=== {message} ===")
        logger.info("="*50)

# Custom JSON encoder for MongoDB ObjectId and Decimal
def custom_json_encoder(obj):
    try:
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return obj
    except Exception as e:
        logger.error(f"Error in custom_json_encoder: {str(e)}")
        logger.error(traceback.format_exc())
        raise

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
ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', 'http://localhost:3000,http://localhost:3001,https://localhost:3002').split(',')
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
    response.headers["Access-Control-Allow-Origin"] = request.headers.get("Origin", ALLOWED_ORIGINS[0]) if request.headers.get("Origin") in ALLOWED_ORIGINS else ALLOWED_ORIGINS[0]
    return response

# Database configuration with connection pooling and retry logic
MONGO_URL = os.getenv('MONGO', 'mongodb://mongo:27017')
MAX_POOL_SIZE = int(os.getenv('MONGO_MAX_POOL_SIZE', '100'))
MIN_POOL_SIZE = int(os.getenv('MONGO_MIN_POOL_SIZE', '10'))
MAX_RETRIES = 5
RETRY_DELAY = 1  # seconds

# Global database variables
db = None
products_collection = None

async def get_database_client() -> AsyncIOMotorClient:
    """Create and return a database client with proper connection settings."""
    client = AsyncIOMotorClient(
        MONGO_URL,
        maxPoolSize=MAX_POOL_SIZE,
        minPoolSize=MIN_POOL_SIZE,
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=5000,
        socketTimeoutMS=10000,
        retryWrites=True,
        w="majority"
    )
    return client

async def init_db():
    """Initialize the database connection with retry logic."""
    global db, products_collection
    
    for attempt in range(MAX_RETRIES):
        try:
            client = await get_database_client()
            # Verify connection is working
            await client.admin.command('ping')
            db = client.confectionery
            
            # Setup collections and indexes
            products_collection = db.get_collection('products')
            
            # Check if collection exists and create if needed
            collections = await db.list_collection_names()
            if 'products' not in collections:
                logger.info("Products collection does not exist. Creating...")
                await db.create_collection('products')
                
            # Create indexes
            existing_indexes = await products_collection.index_information()
            
            if 'name_1' not in existing_indexes:
                await products_collection.create_index([("name", 1)], unique=True)
                logger.info("Created name index on products collection")
                
            if 'category_1' not in existing_indexes:
                await products_collection.create_index([("category", 1)])
                logger.info("Created category index on products collection")
                
            if 'tags_1' not in existing_indexes:
                await products_collection.create_index([("tags", 1)])
                logger.info("Created tags index on products collection")
            
            logger.info("Successfully connected to MongoDB and initialized collections")
            return
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                logger.warning(f"Database connection attempt {attempt + 1} failed: {str(e)}. Retrying in {RETRY_DELAY}s...")
                await asyncio.sleep(RETRY_DELAY)
            else:
                logger.error(f"Failed to connect to database after {MAX_RETRIES} attempts: {str(e)}")
                raise

@app.on_event("startup")
async def startup_event():
    await init_db()
    await create_test_data()

@app.on_event("shutdown")
async def shutdown_event():
    # Motor client cleanup happens automatically
    logger.info("Shutting down application")

# Security configuration
JWT_SECRET = os.getenv('JWT_SECRET')
if not JWT_SECRET or len(JWT_SECRET) < 32:
    logger.error("Insecure or missing SECRET key")
    raise ValueError("SECRET key must be at least 32 characters long")

ALGORITHM = "HS256"

class TokenPayload(BaseModel):
    """Model for JWT token payload validation"""
    sub: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    exp: Optional[datetime] = None
    type: Optional[str] = None

async def verify_token(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """
    Verify the JWT token and return the payload if valid.
    
    Args:
        authorization: The Authorization header containing the JWT token
        
    Returns:
        The decoded token payload
        
    Raises:
        HTTPException: If the token is invalid or expired
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Authorization required',
            headers={"WWW-Authenticate": "Bearer"}
        )
    try:
        scheme, token = authorization.split()
        if scheme.lower() != 'bearer':
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Invalid authentication scheme',
                headers={"WWW-Authenticate": "Bearer"}
            )
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
            
            # Validate token type
            if payload.get("type") != "access":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail='Invalid token type',
                    headers={"WWW-Authenticate": "Bearer"}
                )
                
            # Validate token expiration
            if 'exp' in payload:
                expires_at = datetime.fromtimestamp(payload['exp'])
                if datetime.utcnow() >= expires_at:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail='Token has expired',
                        headers={"WWW-Authenticate": "Bearer"}
                    )
            
            # Validate that required fields are present
            token_data = TokenPayload(**payload)
            if not token_data.sub:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail='Invalid token: missing user ID',
                    headers={"WWW-Authenticate": "Bearer"}
                )
            
            return payload
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f'Invalid token: {str(e)}',
                headers={"WWW-Authenticate": "Bearer"}
            )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid token format',
            headers={"WWW-Authenticate": "Bearer"}
        )
    except Exception as e:
        logger.error(f"Authorization failed: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f'Authorization failed: {str(e)}',
            headers={"WWW-Authenticate": "Bearer"}
        )

def parse_object_id(id: str) -> ObjectId:
    """Safely parse string to ObjectId"""
    try:
        return ObjectId(id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Invalid ID format: {str(e)}'
        )

@app.get('/products', response_model=Dict[str, Any])
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
            log_separator("Count Operation")
            
            # Get total count
            total = await products_collection.count_documents(query)
            logger.info(f"Found {total} documents matching query")
            
            if total == 0:
                logger.info("No documents found, returning empty result")
                return {
                    "total": 0,
                    "products": [],
                    "page": 1,
                    "pages": 0
                }
            
            log_separator("Find Operation")
            
            # Create cursor with sorting and pagination
            cursor = products_collection.find(query)
            
            # Apply sorting
            sort_spec = {sort_field: sort_direction}
            logger.info(f"Sorting with: {sort_spec}")
            cursor = cursor.sort(sort_spec)
            
            # Apply pagination
            cursor = cursor.skip(skip).limit(limit)
            logger.info(f"Applied pagination: skip={skip}, limit={limit}")
            
            # Get products as list
            products = await cursor.to_list(length=limit)
            logger.info(f"Retrieved {len(products)} products")
            
            # Transform products for JSON response
            transformed_products = []
            for product in products:
                # Manual conversion instead of using jsonable_encoder
                product_dict = {}
                for key, value in product.items():
                    if key == '_id':
                        product_dict['id'] = str(value)
                    elif isinstance(value, ObjectId):
                        product_dict[key] = str(value)
                    elif isinstance(value, datetime):
                        product_dict[key] = value.isoformat()
                    elif isinstance(value, Decimal):
                        product_dict[key] = float(value)
                    else:
                        product_dict[key] = value
                
                transformed_products.append(product_dict)
            
            # Build response
            response_data = {
                "total": total,
                "products": transformed_products,
                "page": skip // limit + 1 if limit > 0 else 1,
                "pages": (total + limit - 1) // limit if limit > 0 else 1
            }
            
            log_separator("Request Complete")
            return response_data
            
        except Exception as query_err:
            logger.error(f"Error querying products: {str(query_err)}")
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error querying products: {str(query_err)}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in list_products: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )

@app.get('/products/{product_id}', response_model=Dict[str, Any])
@limiter.limit("60/minute")
async def get_product(request: Request, product_id: str):
    """Get a single product by ID."""
    try:
        product = await products_collection.find_one({'_id': parse_object_id(product_id)})
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Product not found'
            )
        
        # Transform product for JSON response - manually convert MongoDB types
        product_dict = {}
        for key, value in product.items():
            if key == '_id':
                product_dict['id'] = str(value)
            elif isinstance(value, ObjectId):
                product_dict[key] = str(value)
            elif isinstance(value, datetime):
                product_dict[key] = value.isoformat()
            elif isinstance(value, Decimal):
                product_dict[key] = float(value)
            else:
                product_dict[key] = value
        
        return product_dict
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving product: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving product: {str(e)}"
        )

@app.post('/products', status_code=status.HTTP_201_CREATED, response_model=Dict[str, Any])
@limiter.limit("10/minute")
async def create_product(request: Request, product: Product, user: Dict[str, Any] = Depends(verify_token)):
    """Create a new product. Only sellers can create products."""
    if user.get('role', '').lower() not in ['seller', 'admin']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Only sellers and admins can create products'
        )
    
    try:
        # Convert the product to dict and prepare for MongoDB
        product_dict = product.model_dump(exclude={'id'})
        
        # Convert Decimal to float for MongoDB compatibility
        if 'price' in product_dict and isinstance(product_dict['price'], Decimal):
            product_dict['price'] = float(product_dict['price'])
        
        # Validate unique name
        existing = await products_collection.find_one({'name': product_dict['name']})
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail='Product with this name already exists'
            )
        
        # Add metadata
        product_dict['created_by'] = user.get('sub')
        product_dict['created_at'] = datetime.utcnow()
        product_dict['updated_at'] = datetime.utcnow()
        
        # Insert into MongoDB
        result = await products_collection.insert_one(product_dict)
        
        # Return the created product
        created_product = await products_collection.find_one({'_id': result.inserted_id})
        
        # Transform product for JSON response - manually convert MongoDB types
        product_dict = {}
        for key, value in created_product.items():
            if key == '_id':
                product_dict['id'] = str(value)
            elif isinstance(value, ObjectId):
                product_dict[key] = str(value)
            elif isinstance(value, datetime):
                product_dict[key] = value.isoformat()
            elif isinstance(value, Decimal):
                product_dict[key] = float(value)
            else:
                product_dict[key] = value
        
        return product_dict
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating product: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating product: {str(e)}"
        )

@app.put('/products/{product_id}', response_model=Dict[str, Any])
@limiter.limit("20/minute")
async def update_product(
    request: Request,
    product_id: str,
    product: Product,
    user: Dict[str, Any] = Depends(verify_token)
):
    """Update an existing product. Only sellers can update products."""
    if user.get('role', '').lower() not in ['seller', 'admin']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Only sellers and admins can update products'
        )
    
    try:
        # Get existing product
        existing = await products_collection.find_one({'_id': parse_object_id(product_id)})
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Product not found'
            )
        
        # Check ownership (admins can update any product)
        if user.get('role', '').lower() != 'admin' and existing.get('created_by') != user.get('sub'):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='You can only update your own products'
            )
        
        # Convert the product to dict and prepare for MongoDB
        product_dict = product.model_dump(exclude={'id'})
        
        # Convert Decimal to float for MongoDB compatibility
        if 'price' in product_dict and isinstance(product_dict['price'], Decimal):
            product_dict['price'] = float(product_dict['price'])
        
        # Check name uniqueness if changed
        if product_dict['name'] != existing['name']:
            name_exists = await products_collection.find_one({
                '_id': {'$ne': parse_object_id(product_id)},
                'name': product_dict['name']
            })
            if name_exists:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail='Product with this name already exists'
                )
        
        # Preserve metadata and update timestamp
        product_dict['created_by'] = existing['created_by']
        product_dict['created_at'] = existing['created_at']
        product_dict['updated_at'] = datetime.utcnow()
        product_dict['updated_by'] = user.get('sub')
        
        # Update in MongoDB
        result = await products_collection.replace_one(
            {'_id': parse_object_id(product_id)},
            product_dict
        )
        
        if result.modified_count == 0:
            # If no modifications were made, return the existing document
            # This avoids 304 Not Modified which may confuse clients
            updated_product = await products_collection.find_one({'_id': parse_object_id(product_id)})
        else:
            # Return the updated product
            updated_product = await products_collection.find_one({'_id': parse_object_id(product_id)})
        
        # Transform product for JSON response - manually convert MongoDB types
        product_dict = {}
        for key, value in updated_product.items():
            if key == '_id':
                product_dict['id'] = str(value)
            elif isinstance(value, ObjectId):
                product_dict[key] = str(value)
            elif isinstance(value, datetime):
                product_dict[key] = value.isoformat()
            elif isinstance(value, Decimal):
                product_dict[key] = float(value)
            else:
                product_dict[key] = value
        
        return product_dict
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating product: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating product: {str(e)}"
        )

@app.delete('/products/{product_id}', response_model=Dict[str, str])
@limiter.limit("10/minute")
async def delete_product(
    request: Request,
    product_id: str,
    user: Dict[str, Any] = Depends(verify_token)
):
    """Delete a product. Only sellers can delete their own products."""
    if user.get('role', '').lower() not in ['seller', 'admin']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Only sellers and admins can delete products'
        )
    
    try:
        # Get existing product
        existing = await products_collection.find_one({'_id': parse_object_id(product_id)})
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Product not found'
            )
        
        # Check ownership (admins can delete any product)
        if user.get('role', '').lower() != 'admin' and existing.get('created_by') != user.get('sub'):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='You can only delete your own products'
            )
        
        result = await products_collection.delete_one({'_id': parse_object_id(product_id)})
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Product not found'
            )
        return {
            'message': 'Product deleted successfully',
            'id': product_id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting product: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting product: {str(e)}"
        )

@app.get('/categories', response_model=List[str])
@limiter.limit("30/minute")
async def list_categories(request: Request):
    """Get a list of all unique product categories."""
    try:
        categories = await products_collection.distinct('category')
        return sorted(categories)
    except Exception as e:
        logger.error(f"Error retrieving categories: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving categories: {str(e)}"
        )

@app.get('/tags', response_model=List[str])
@limiter.limit("30/minute")
async def list_tags(request: Request):
    """Get a list of all unique product tags."""
    try:
        tags = await products_collection.distinct('tags')
        return sorted(tags)
    except Exception as e:
        logger.error(f"Error retrieving tags: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
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
                },
                {
                    "name": "Strawberry Tart",
                    "description": "Fresh strawberry tart with custard filling",
                    "price": 24.99,
                    "category": "Pastries",
                    "is_available": True,
                    "image_url": "https://example.com/strawberry-tart.jpg",
                    "tags": ["strawberry", "tart", "pastry", "fruit"],
                    "recipe": [
                        {"ingredient": "flour", "quantity": 2.0, "unit": "cups"},
                        {"ingredient": "strawberries", "quantity": 1.0, "unit": "cups"},
                        {"ingredient": "sugar", "quantity": 0.5, "unit": "cups"}
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
        logger.error(traceback.format_exc())

@app.get("/health", response_model=Dict[str, Any])
async def health_check():
    """Check service health"""
    try:
        # Check database connection
        await db.command('ping')
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service unhealthy"
        )
