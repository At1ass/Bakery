from fastapi import FastAPI, Depends, HTTPException, Header, Query, Request, status
from motor.motor_asyncio import AsyncIOMotorClient
from models import Order, OrderItem, OrderStatus, PyObjectId
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
import os, aiohttp, asyncio, logging, traceback, json
from jose import jwt, JWTError
from typing import Optional, List, Dict, Any, Union
from bson.objectid import ObjectId
from datetime import datetime, timedelta
from decimal import Decimal
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

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
        if isinstance(obj, dict):
            return {key: custom_json_encoder(value) for key, value in obj.items()}
        if isinstance(obj, list):
            return [custom_json_encoder(item) for item in obj]
        return obj
    except Exception as e:
        logger.error(f"Error in custom_json_encoder: {str(e)}")
        logger.error(traceback.format_exc())
        raise

def convert_decimals_to_float(obj):
    """Recursively convert Decimal objects to float for MongoDB compatibility"""
    if isinstance(obj, Decimal):
        logger.info(f"Converting Decimal {obj} to float {float(obj)}")
        return float(obj)
    elif isinstance(obj, dict):
        return {key: convert_decimals_to_float(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimals_to_float(item) for item in obj]
    else:
        return obj

def ensure_no_decimals(obj, path="root"):
    """Recursively check for any Decimal objects and log their location"""
    if isinstance(obj, Decimal):
        logger.error(f"Found Decimal object at {path}: {obj} (type: {type(obj)})")
        return False
    elif isinstance(obj, dict):
        for key, value in obj.items():
            if not ensure_no_decimals(value, f"{path}.{key}"):
                return False
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            if not ensure_no_decimals(item, f"{path}[{i}]"):
                return False
    return True

# Initialize FastAPI app with documentation settings
app = FastAPI(
    title="Order Service",
    description="Service for managing confectionery orders",
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
    response.headers["Access-Control-Allow-Origin"] = request.headers.get("Origin", ALLOWED_ORIGINS[0]) if request.headers.get("Origin") in ALLOWED_ORIGINS else ALLOWED_ORIGINS[0]
    return response

# Error handling middleware
@app.middleware("http")
async def exception_handling(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}")
        logger.error(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal Server Error", "message": str(e)}
        )

# Database configuration with connection pooling and retry logic
MONGO_URL = os.getenv('MONGO', 'mongodb://mongo:27017')
MAX_POOL_SIZE = int(os.getenv('MONGO_MAX_POOL_SIZE', '100'))
MIN_POOL_SIZE = int(os.getenv('MONGO_MIN_POOL_SIZE', '10'))
MAX_RETRIES = 5
RETRY_DELAY = 1  # seconds

# Global database variables
db = None
orders_collection = None

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
    global db, orders_collection
    
    for attempt in range(MAX_RETRIES):
        try:
            client = await get_database_client()
            # Verify connection is working
            await client.admin.command('ping')
            
            db = client.confectionery
            orders_collection = db.get_collection('orders')
            
            # Check if collection exists and create if needed
            collections = await db.list_collection_names()
            if 'orders' not in collections:
                logger.info("Orders collection does not exist. Creating...")
                await db.create_collection('orders')
            
            # Create indexes
            existing_indexes = await orders_collection.index_information()
            
            if 'user_id_1' not in existing_indexes:
                await orders_collection.create_index([("user_id", 1)])
                logger.info("Created user_id index on orders collection")
                
            if 'status_1' not in existing_indexes:
                await orders_collection.create_index([("status", 1)])
                logger.info("Created status index on orders collection")
                
            if 'created_at_-1' not in existing_indexes:
                await orders_collection.create_index([("created_at", -1)])
                logger.info("Created created_at index on orders collection")
            
            logger.info("Successfully connected to MongoDB and initialized collections")
            return
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                logger.warning(f"Database connection attempt {attempt + 1} failed: {str(e)}. Retrying in {RETRY_DELAY}s...")
                await asyncio.sleep(RETRY_DELAY)
            else:
                logger.error(f"Failed to connect to database after {MAX_RETRIES} attempts: {str(e)}")
                logger.error(traceback.format_exc())
                raise

@app.on_event("startup")
async def startup_event():
    await init_db()

@app.on_event("shutdown")
async def shutdown_event():
    # Motor client cleanup happens automatically
    logger.info("Shutting down application")

# Service configuration
JWT_SECRET = os.getenv('JWT_SECRET')
if not JWT_SECRET or len(JWT_SECRET) < 32:
    logger.error("Insecure or missing JWT_SECRET key")
    raise ValueError("JWT_SECRET key must be at least 32 characters long")

ALGORITHM = "HS256"
CATALOG_URL = os.getenv('CATALOG_URL', 'http://catalog:8000')
CATALOG_TIMEOUT = int(os.getenv('CATALOG_TIMEOUT', '5'))  # seconds
AUTH_URL = os.getenv('AUTH_URL', 'http://auth:8000')
AUTH_TIMEOUT = int(os.getenv('AUTH_TIMEOUT', '5'))  # seconds

# Token model for validation
class TokenPayload:
    def __init__(self, data: Dict[str, Any]):
        self.sub = data.get("sub")
        self.email = data.get("email")
        self.role = data.get("role")
        self.exp = data.get("exp")
        self.type = data.get("type")

# Utility functions
def parse_object_id(id: str) -> ObjectId:
    """Safely parse string to ObjectId"""
    try:
        return ObjectId(id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Invalid ID format: {str(e)}'
        )

async def verify_token(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """Verify JWT token and return payload"""
    logger.info(f"Authorization header received: '{authorization}'")
    
    if not authorization:
        logger.warning("No authorization header provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Authorization required',
            headers={"WWW-Authenticate": "Bearer"}
        )
    try:
        logger.info(f"Attempting to split authorization header: '{authorization}'")
        scheme, token = authorization.split()
        logger.info(f"Scheme: '{scheme}', Token: '{token[:20]}...' (showing first 20 chars)")
        
        if scheme.lower() != 'bearer':
            logger.warning(f"Invalid authentication scheme: '{scheme}'")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Invalid authentication scheme',
                headers={"WWW-Authenticate": "Bearer"}
            )
        try:
            logger.info(f"Attempting to decode JWT token")
            payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
            
            # Validate token type
            if payload.get("type") != "access":
                logger.warning(f"Invalid token type: {payload.get('type')}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail='Invalid token type',
                    headers={"WWW-Authenticate": "Bearer"}
                )
                
            # Validate token expiration
            if 'exp' in payload:
                expires_at = datetime.fromtimestamp(payload['exp'])
                if datetime.utcnow() >= expires_at:
                    logger.warning(f"Token has expired at {expires_at}")
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail='Token has expired',
                        headers={"WWW-Authenticate": "Bearer"}
                    )
            
            # Validate that required fields are present
            token_data = TokenPayload(payload)
            if not token_data.sub:
                logger.warning("Token missing user ID")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail='Invalid token: missing user ID',
                    headers={"WWW-Authenticate": "Bearer"}
                )
            
            logger.info(f"Token validated successfully for user: {token_data.sub}")
            return payload
        except JWTError as e:
            logger.error(f"JWT decode error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f'Invalid token: {str(e)}',
                headers={"WWW-Authenticate": "Bearer"}
            )
    except ValueError as e:
        logger.error(f"Authorization header split error: {str(e)}")
        logger.error(f"Authorization header value: '{authorization}'")
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

async def get_user_details(user_id: str, session: aiohttp.ClientSession, token: str) -> Dict[str, Any]:
    """Fetch user details from auth service"""
    try:
        async with session.get(
            f"{AUTH_URL}/users/{user_id}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=AUTH_TIMEOUT
        ) as response:
            if response.status == 404:
                logger.warning(f"User {user_id} not found in auth service")
                return None
            elif response.status == 403:
                logger.warning(f"Access denied when fetching user {user_id}")
                return None
            elif response.status != 200:
                logger.error(f"Auth service returned status {response.status}")
                return None
            
            user_data = await response.json()
            return user_data
    except asyncio.TimeoutError:
        logger.error(f"Timeout when connecting to auth service")
        return None
    except aiohttp.ClientError as e:
        logger.error(f"Error connecting to auth service: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching user details: {str(e)}")
        return None

async def get_product_details(product_id: str, session: aiohttp.ClientSession) -> Dict[str, Any]:
    """Fetch product details from catalog service"""
    try:
        async with session.get(
            f"{CATALOG_URL}/products/{product_id}",
            timeout=CATALOG_TIMEOUT
        ) as response:
            if response.status == 404:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f'Product {product_id} not found'
                )
            elif response.status != 200:
                logger.error(f"Catalog service returned status {response.status}")
                try:
                    error_data = await response.json()
                    logger.error(f"Catalog service error: {error_data}")
                except:
                    logger.error(f"Could not parse catalog service error response")
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail='Error fetching product information'
                )
            
            # Get the product data and convert all Decimal objects to float
            product_data = await response.json()
            # Use our convert_decimals_to_float function to handle any Decimal objects
            product_data = convert_decimals_to_float(product_data)
            return product_data
    except asyncio.TimeoutError:
        logger.error(f"Timeout when connecting to catalog service")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail='Catalog service timeout'
        )
    except aiohttp.ClientError as e:
        logger.error(f"Error connecting to catalog service: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f'Error communicating with catalog service: {str(e)}'
        )

@app.post('/orders', status_code=status.HTTP_201_CREATED, response_model=Dict[str, Any])
@limiter.limit("10/minute")
async def create_order(request: Request, order: Order, user: Dict[str, Any] = Depends(verify_token)):
    """Create a new order"""
    try:
        log_separator("Creating new order")
        # Initialize order metadata
        order_dict = order.model_dump(exclude={'id'})
        order_dict['user_id'] = user.get('sub')
        order_dict['created_at'] = datetime.utcnow()
        order_dict['updated_at'] = datetime.utcnow()
        order_dict['status'] = OrderStatus.PENDING
        
        # Calculate estimated delivery time (2 hours from now)
        order_dict['estimated_delivery'] = datetime.utcnow() + timedelta(hours=2)
        
        # Fetch product details and calculate totals
        total = 0.0  # Use float instead of Decimal
        async with aiohttp.ClientSession() as session:
            for item in order_dict['items']:
                logger.info(f"Fetching details for product {item['product_id']}")
                product = await get_product_details(item['product_id'], session)
                logger.info(f"Product data received: {product}")
                
                item['product_name'] = product['name']
                
                # Convert price to float immediately and avoid Decimal altogether
                price = float(product['price'])
                quantity = int(item['quantity'])
                
                logger.info(f"Processing item: price={price} (type: {type(price)}), quantity={quantity}")
                
                item['unit_price'] = price
                item['total_price'] = price * quantity
                total += price * quantity
                
                logger.info(f"Item processed: unit_price={item['unit_price']}, total_price={item['total_price']}")
        
        order_dict['total'] = total
        logger.info(f"Order total calculated: {total} (type: {type(total)})")
        
        # Convert any remaining Decimal objects to float for MongoDB compatibility
        logger.info("Converting any remaining Decimal objects to float")
        order_dict = convert_decimals_to_float(order_dict)
        logger.info(f"Order dict after conversion: {order_dict}")
        
        # Final check for any remaining Decimal objects
        logger.info("Performing final check for Decimal objects")
        if not ensure_no_decimals(order_dict, "order_dict"):
            logger.error("Found Decimal objects in order data after conversion!")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal error: Decimal objects found in order data"
            )
        
        # Insert order
        logger.info(f"Inserting order into database")
        try:
            result = await orders_collection.insert_one(order_dict)
            logger.info(f"Order inserted successfully with ID: {result.inserted_id}")
        except Exception as insert_error:
            logger.error(f"Error inserting order into database: {str(insert_error)}")
            logger.error(f"Order dict that failed to insert: {order_dict}")
            # Additional debugging: check the exact type of each value
            for key, value in order_dict.items():
                logger.error(f"  {key}: {value} (type: {type(value)})")
                if isinstance(value, list):
                    for i, item in enumerate(value):
                        logger.error(f"    [{i}]: {item} (type: {type(item)})")
                        if isinstance(item, dict):
                            for subkey, subvalue in item.items():
                                logger.error(f"      {subkey}: {subvalue} (type: {type(subvalue)})")
            raise
        
        # Return created order
        created_order = await orders_collection.find_one({'_id': result.inserted_id})
        created_order['id'] = str(created_order.pop('_id'))
        
        # Convert any remaining problematic types using our custom encoder
        response_data = custom_json_encoder(created_order)
        
        logger.info(f"Created order with ID: {response_data['id']}")
        log_separator("Order creation complete")
        
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=response_data
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating order: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating order: {str(e)}"
        )

@app.get('/orders', response_model=Dict[str, Any])
@limiter.limit("30/minute")
async def list_orders(
    request: Request,
    user: Dict[str, Any] = Depends(verify_token),
    skip: int = Query(0, ge=0, description="Number of orders to skip"),
    limit: int = Query(10, ge=1, le=100, description="Number of orders to return"),
    order_status: Optional[OrderStatus] = Query(None, description="Filter by order status"),
    from_date: Optional[datetime] = Query(None, description="Filter orders from this date"),
    to_date: Optional[datetime] = Query(None, description="Filter orders until this date"),
    min_total: Optional[float] = Query(None, ge=0, description="Minimum order total"),
    max_total: Optional[float] = Query(None, gt=0, description="Maximum order total")
):
    """List orders with filtering and pagination"""
    try:
        log_separator("Listing orders")
        
        # Build query
        query = {}
        if user.get('role') == 'customer':
            query['user_id'] = user.get('sub')
        if order_status:
            query['status'] = order_status
        if from_date:
            query.setdefault('created_at', {})['$gte'] = from_date
        if to_date:
            query.setdefault('created_at', {})['$lte'] = to_date
        if min_total is not None:
            query.setdefault('total', {})['$gte'] = min_total
        if max_total is not None:
            query.setdefault('total', {})['$lte'] = max_total

        logger.info(f"Query filters: {query}")
        logger.info(f"Pagination: skip={skip}, limit={limit}")

        # Get total count
        total = await orders_collection.count_documents(query)
        logger.info(f"Found {total} matching orders")
        
        if total == 0:
            return JSONResponse(content={
                "total": 0,
                "orders": [],
                "page": 1,
                "pages": 0
            })

        # Get paginated results
        cursor = orders_collection.find(query)
        cursor.sort('created_at', -1)
        cursor.skip(skip).limit(limit)
        orders = await cursor.to_list(length=limit)
        
        # Transform ObjectId to string and handle datetime serialization
        transformed_orders = []
        
        # For sellers, fetch customer email information
        logger.info(f"User role: {user.get('role')}, Orders count: {len(orders)}")
        if user.get('role') in ['Seller', 'Admin'] and orders:
            logger.info("Fetching customer email information for seller")
            async with aiohttp.ClientSession() as session:
                # Create a token for the current request
                current_token = request.headers.get('authorization', '').replace('Bearer ', '')
                logger.info(f"Using token for auth service: {current_token[:20]}...")
                
                for order in orders:
                    order['id'] = str(order.pop('_id'))
                    
                    # Try to fetch customer email
                    if order.get('user_id'):
                        logger.info(f"Fetching user details for user_id: {order['user_id']}")
                        user_details = await get_user_details(order['user_id'], session, current_token)
                        if user_details:
                            logger.info(f"Got user details: {user_details}")
                            order['customer_email'] = user_details.get('email', 'Unknown')
                        else:
                            logger.warning(f"Could not fetch user details for {order['user_id']}")
                            order['customer_email'] = f"User {order['user_id'][-8:]}"
                    
                    # Use custom encoder to handle datetime objects
                    transformed_orders.append(custom_json_encoder(order))
        else:
            logger.info("Not fetching customer emails (customer user or no orders)")
            # For customers or when no orders, just transform without fetching emails
            for order in orders:
                order['id'] = str(order.pop('_id'))
                # Use custom encoder to handle datetime objects
                transformed_orders.append(custom_json_encoder(order))
        
        response = {
            "total": total,
            "orders": transformed_orders,
            "page": skip // limit + 1 if limit > 0 else 1,
            "pages": (total + limit - 1) // limit if limit > 0 else 1
        }
        
        log_separator("Orders list request complete")
        return Response(
            content=json.dumps(response, default=custom_json_encoder),
            media_type="application/json"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing orders: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing orders: {str(e)}"
        )

@app.get('/orders/{order_id}', response_model=Dict[str, Any])
@limiter.limit("60/minute")
async def get_order(
    request: Request,
    order_id: str,
    user: Dict[str, Any] = Depends(verify_token)
):
    """Get a single order by ID"""
    try:
        logger.info(f"Fetching order with ID: {order_id}")
        order = await orders_collection.find_one({'_id': parse_object_id(order_id)})
        if not order:
            logger.warning(f"Order not found: {order_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Order not found'
            )
        
        # Check authorization
        if user.get('role') == 'customer' and order['user_id'] != user.get('sub'):
            logger.warning(f"Access denied: User {user.get('sub')} attempted to access order {order_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Access denied'
            )
        
        order['id'] = str(order.pop('_id'))
        logger.info(f"Order {order_id} fetched successfully")
        return Response(
            content=json.dumps(order, default=custom_json_encoder),
            media_type="application/json"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving order: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving order: {str(e)}"
        )

@app.put('/orders/{order_id}/status', response_model=Dict[str, Any])
@limiter.limit("20/minute")
async def update_order_status(
    request: Request,
    order_id: str,
    new_status: OrderStatus,
    user: Dict[str, Any] = Depends(verify_token)
):
    """Update order status (sellers only)"""
    if user.get('role') not in ['seller', 'admin']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Only sellers and admins can update order status'
        )
    
    try:
        log_separator(f"Updating order {order_id} status to {new_status}")
        
        # Get existing order
        order = await orders_collection.find_one({'_id': parse_object_id(order_id)})
        if not order:
            logger.warning(f"Order not found: {order_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Order not found'
            )
        
        # Validate status transition
        current_status = OrderStatus(order['status'])
        if not is_valid_status_transition(current_status, new_status):
            logger.warning(f"Invalid status transition: {current_status} → {new_status}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f'Invalid status transition from {current_status} to {new_status}'
            )
        
        # Update status
        logger.info(f"Updating order status in database")
        result = await orders_collection.update_one(
            {'_id': parse_object_id(order_id)},
            {
                '$set': {
                    'status': new_status,
                    'updated_at': datetime.utcnow(),
                    'updated_by': user.get('sub')
                }
            }
        )
        
        if result.modified_count == 0:
            logger.warning(f"Order status not modified: {order_id}")
            return JSONResponse(
                status_code=status.HTTP_304_NOT_MODIFIED,
                content={'detail': 'Order status not modified'}
            )
        
        # Return updated order
        updated_order = await orders_collection.find_one({'_id': parse_object_id(order_id)})
        updated_order['id'] = str(updated_order.pop('_id'))
        
        logger.info(f"Order status updated successfully")
        log_separator("Status update complete")
        
        return Response(
            content=json.dumps(updated_order, default=custom_json_encoder),
            media_type="application/json"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating order status: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating order status: {str(e)}"
        )

def is_valid_status_transition(current: OrderStatus, new: OrderStatus) -> bool:
    """Validate order status transitions"""
    valid_transitions = {
        OrderStatus.PENDING: {OrderStatus.CONFIRMED, OrderStatus.CANCELLED},
        OrderStatus.CONFIRMED: {OrderStatus.PREPARING, OrderStatus.CANCELLED},
        OrderStatus.PREPARING: {OrderStatus.READY},
        OrderStatus.READY: {OrderStatus.COMPLETED},
        OrderStatus.COMPLETED: set(),  # No transitions from completed
        OrderStatus.CANCELLED: set()  # No transitions from cancelled
    }
    return new in valid_transitions.get(current, set())

@app.delete('/orders/{order_id}', response_model=Dict[str, str])
@limiter.limit("10/minute")
async def cancel_order(
    request: Request,
    order_id: str,
    user: Dict[str, Any] = Depends(verify_token)
):
    """Cancel an order (if it's in PENDING or CONFIRMED status)"""
    try:
        log_separator(f"Cancelling order {order_id}")
        
        # Get existing order
        order = await orders_collection.find_one({'_id': parse_object_id(order_id)})
        if not order:
            logger.warning(f"Order not found: {order_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Order not found'
            )
        
        # Check authorization
        if user.get('role') == 'customer' and order['user_id'] != user.get('sub'):
            logger.warning(f"Access denied: User {user.get('sub')} attempted to cancel order {order_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Access denied'
            )
        
        # Check if order can be cancelled
        current_status = OrderStatus(order['status'])
        if current_status not in {OrderStatus.PENDING, OrderStatus.CONFIRMED}:
            logger.warning(f"Cannot cancel order in {current_status} status")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f'Cannot cancel order in {current_status} status'
            )
        
        # Update status to cancelled
        logger.info(f"Updating order status to cancelled")
        result = await orders_collection.update_one(
            {'_id': parse_object_id(order_id)},
            {
                '$set': {
                    'status': OrderStatus.CANCELLED,
                    'updated_at': datetime.utcnow(),
                    'cancelled_by': user.get('sub'),
                    'cancellation_reason': 'User requested cancellation'
                }
            }
        )
        
        if result.modified_count == 0:
            logger.warning(f"Order not modified: {order_id}")
            return JSONResponse(
                status_code=status.HTTP_304_NOT_MODIFIED,
                content={'detail': 'Order not modified'}
            )
        
        logger.info(f"Order cancelled successfully")
        log_separator("Cancellation complete")
        
        return JSONResponse(
            content={'message': 'Order cancelled successfully', 'id': order_id},
            status_code=status.HTTP_200_OK
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling order: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error cancelling order: {str(e)}"
        )

@app.get("/health", response_model=Dict[str, Any])
async def health_check():
    """Check service health"""
    try:
        # Check database connection
        await db.command('ping')
        
        # Check catalog service
        catalog_status = "unknown"
        try:
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(
                        f"{CATALOG_URL}/health",
                        timeout=CATALOG_TIMEOUT
                    ) as response:
                        catalog_status = "connected" if response.status == 200 else "error"
                except Exception as e:
                    logger.warning(f"Could not connect to catalog service: {str(e)}")
                    catalog_status = "error"
        except Exception as e:
            logger.warning(f"Error creating aiohttp session: {str(e)}")
            catalog_status = "error"
        
        return JSONResponse(
            content={
                "status": "healthy",
                "database": "connected",
                "catalog_service": catalog_status,
                "timestamp": datetime.utcnow().isoformat(),
                "version": "1.0.0"
            }
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        logger.error(traceback.format_exc())
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "detail": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )
