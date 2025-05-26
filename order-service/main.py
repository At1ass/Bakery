from fastapi import FastAPI, Depends, HTTPException, Header, Query, Request
from motor.motor_asyncio import AsyncIOMotorClient
from models import Order, OrderItem, OrderStatus
from fastapi.middleware.cors import CORSMiddleware
import os, aiohttp, asyncio, logging
from jose import jwt
from typing import Optional, List
from bson.objectid import ObjectId
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
from decimal import Decimal
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    return response

# Database configuration with connection pooling and retry logic
MONGO_URL = os.getenv('MONGO', 'mongodb://mongo:27017/confectionery')
MAX_POOL_SIZE = int(os.getenv('MONGO_MAX_POOL_SIZE', '100'))
MIN_POOL_SIZE = int(os.getenv('MONGO_MIN_POOL_SIZE', '10'))
MAX_RETRIES = 3

# Global database variables
db = None
orders_collection = None

async def init_db():
    global db, orders_collection
    
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
        orders_collection = db.get_collection('orders')
        # Create indexes
        await orders_collection.create_index([("user_id", 1)])
        await orders_collection.create_index([("status", 1)])
        await orders_collection.create_index([("created_at", -1)])
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

@app.on_event("startup")
async def startup_event():
    await init_db()

@app.on_event("shutdown")
async def shutdown_event():
    if 'client' in globals():
        client.close()
        logger.info("Closed MongoDB connection")

# Service configuration
SECRET = os.getenv('SECRET')
if not SECRET or len(SECRET) < 32:
    logger.error("Insecure or missing SECRET key")
    raise ValueError("SECRET key must be at least 32 characters long")

CATALOG_URL = os.getenv('CATALOG_URL', 'http://catalog:8000')
CATALOG_TIMEOUT = int(os.getenv('CATALOG_TIMEOUT', '5'))  # seconds

# Utility functions
def parse_object_id(id: str) -> ObjectId:
    """Safely parse string to ObjectId"""
    try:
        return ObjectId(id)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f'Invalid ID format: {str(e)}'
        )

async def verify_token(authorization: Optional[str] = Header(None)) -> dict:
    """Verify JWT token and return payload"""
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

async def get_product_details(product_id: str, session: aiohttp.ClientSession) -> dict:
    """Fetch product details from catalog service"""
    try:
        async with session.get(
            f"{CATALOG_URL}/products/{product_id}",
            timeout=CATALOG_TIMEOUT
        ) as response:
            if response.status == 404:
                raise HTTPException(
                    status_code=400,
                    detail=f'Product {product_id} not found'
                )
            elif response.status != 200:
                raise HTTPException(
                    status_code=502,
                    detail='Error fetching product information'
                )
            return await response.json()
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=504,
            detail='Catalog service timeout'
        )
    except aiohttp.ClientError as e:
        raise HTTPException(
            status_code=502,
            detail=f'Error communicating with catalog service: {str(e)}'
        )

@app.post('/orders')
@limiter.limit("10/minute")
async def create_order(request: Request, order: Order, user: dict = Depends(verify_token)):
    """Create a new order"""
    try:
        # Initialize order metadata
        order_dict = order.dict(exclude={'id', 'user_id', 'total'})
        order_dict['user_id'] = user.get('sub')
        order_dict['created_at'] = datetime.utcnow()
        order_dict['updated_at'] = datetime.utcnow()
        order_dict['status'] = OrderStatus.PENDING
        
        # Calculate estimated delivery time (2 hours from now)
        order_dict['estimated_delivery'] = datetime.utcnow() + timedelta(hours=2)
        
        # Fetch product details and calculate totals
        total = Decimal('0')
        async with aiohttp.ClientSession() as session:
            for item in order_dict['items']:
                product = await get_product_details(item['product_id'], session)
                item['product_name'] = product['name']
                item['unit_price'] = Decimal(str(product['price']))
                item['total_price'] = item['unit_price'] * item['quantity']
                total += item['total_price']
        
        order_dict['total'] = float(total)  # Convert Decimal to float for MongoDB
        
        # Insert order
        result = await orders_collection.insert_one(order_dict)
        
        # Return created order
        created_order = await orders_collection.find_one({'_id': result.inserted_id})
        created_order['id'] = str(created_order.pop('_id'))
        
        return JSONResponse(
            status_code=201,
            content=created_order
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating order: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error creating order: {str(e)}"
        )

@app.get('/orders')
@limiter.limit("30/minute")
async def list_orders(
    request: Request,
    user: dict = Depends(verify_token),
    skip: int = Query(0, ge=0, description="Number of orders to skip"),
    limit: int = Query(10, ge=1, le=100, description="Number of orders to return"),
    status: Optional[OrderStatus] = Query(None, description="Filter by order status"),
    from_date: Optional[datetime] = Query(None, description="Filter orders from this date"),
    to_date: Optional[datetime] = Query(None, description="Filter orders until this date"),
    min_total: Optional[float] = Query(None, ge=0, description="Minimum order total"),
    max_total: Optional[float] = Query(None, gt=0, description="Maximum order total")
):
    """List orders with filtering and pagination"""
    try:
        # Build query
        query = {}
        if user.get('role') == 'customer':
            query['user_id'] = user.get('sub')
        if status:
            query['status'] = status
        if from_date:
            query.setdefault('created_at', {})['$gte'] = from_date
        if to_date:
            query.setdefault('created_at', {})['$lte'] = to_date
        if min_total is not None:
            query.setdefault('total', {})['$gte'] = min_total
        if max_total is not None:
            query.setdefault('total', {})['$lte'] = max_total

        # Get total count
        total = await orders_collection.count_documents(query)
        
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
        
        # Transform ObjectId to string
        transformed_orders = []
        for order in orders:
            order['id'] = str(order.pop('_id'))
            transformed_orders.append(order)
        
        return JSONResponse(content={
            "total": total,
            "orders": transformed_orders,
            "page": skip // limit + 1,
            "pages": (total + limit - 1) // limit
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing orders: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error listing orders: {str(e)}"
        )

@app.get('/orders/{order_id}')
@limiter.limit("60/minute")
async def get_order(
    request: Request,
    order_id: str,
    user: dict = Depends(verify_token)
):
    """Get a single order by ID"""
    try:
        order = await orders_collection.find_one({'_id': parse_object_id(order_id)})
        if not order:
            raise HTTPException(
                status_code=404,
                detail='Order not found'
            )
        
        # Check authorization
        if user.get('role') == 'customer' and order['user_id'] != user.get('sub'):
            raise HTTPException(
                status_code=403,
                detail='Access denied'
            )
        
        order['id'] = str(order.pop('_id'))
        return JSONResponse(content=order)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving order: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving order: {str(e)}"
        )

@app.put('/orders/{order_id}/status')
@limiter.limit("20/minute")
async def update_order_status(
    request: Request,
    order_id: str,
    status: OrderStatus,
    user: dict = Depends(verify_token)
):
    """Update order status (sellers only)"""
    if user.get('role') != 'seller':
        raise HTTPException(
            status_code=403,
            detail='Only sellers can update order status'
        )
    
    try:
        # Get existing order
        order = await orders_collection.find_one({'_id': parse_object_id(order_id)})
        if not order:
            raise HTTPException(
                status_code=404,
                detail='Order not found'
            )
        
        # Validate status transition
        current_status = OrderStatus(order['status'])
        if not is_valid_status_transition(current_status, status):
            raise HTTPException(
                status_code=400,
                detail=f'Invalid status transition from {current_status} to {status}'
            )
        
        # Update status
        result = await orders_collection.update_one(
            {'_id': parse_object_id(order_id)},
            {
                '$set': {
                    'status': status,
                    'updated_at': datetime.utcnow()
                }
            }
        )
        
        if result.modified_count == 0:
            raise HTTPException(
                status_code=304,
                detail='Order status not modified'
            )
        
        # Return updated order
        updated_order = await orders_collection.find_one({'_id': parse_object_id(order_id)})
        updated_order['id'] = str(updated_order.pop('_id'))
        return JSONResponse(content=updated_order)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating order status: {str(e)}")
        raise HTTPException(
            status_code=500,
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

@app.delete('/orders/{order_id}')
@limiter.limit("10/minute")
async def cancel_order(
    request: Request,
    order_id: str,
    user: dict = Depends(verify_token)
):
    """Cancel an order (if it's in PENDING or CONFIRMED status)"""
    try:
        # Get existing order
        order = await orders_collection.find_one({'_id': parse_object_id(order_id)})
        if not order:
            raise HTTPException(
                status_code=404,
                detail='Order not found'
            )
        
        # Check authorization
        if user.get('role') == 'customer' and order['user_id'] != user.get('sub'):
            raise HTTPException(
                status_code=403,
                detail='Access denied'
            )
        
        # Check if order can be cancelled
        current_status = OrderStatus(order['status'])
        if current_status not in {OrderStatus.PENDING, OrderStatus.CONFIRMED}:
            raise HTTPException(
                status_code=400,
                detail=f'Cannot cancel order in {current_status} status'
            )
        
        # Update status to cancelled
        result = await orders_collection.update_one(
            {'_id': parse_object_id(order_id)},
            {
                '$set': {
                    'status': OrderStatus.CANCELLED,
                    'updated_at': datetime.utcnow()
                }
            }
        )
        
        if result.modified_count == 0:
            raise HTTPException(
                status_code=304,
                detail='Order not modified'
            )
        
        return JSONResponse(
            content={'message': 'Order cancelled successfully'},
            status_code=200
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling order: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error cancelling order: {str(e)}"
        )

@app.get("/health")
async def health_check():
    """Check service health"""
    try:
        # Check database connection
        await db.command('ping')
        
        # Check catalog service
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    f"{CATALOG_URL}/health",
                    timeout=CATALOG_TIMEOUT
                ) as response:
                    catalog_status = "connected" if response.status == 200 else "error"
            except:
                catalog_status = "error"
        
        return JSONResponse(
            content={
                "status": "healthy",
                "database": "connected",
                "catalog_service": catalog_status,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail="Service unhealthy"
        )
