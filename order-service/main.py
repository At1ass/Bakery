from fastapi import FastAPI, Depends, HTTPException, Header, Query
from motor.motor_asyncio import AsyncIOMotorClient
from models import Order, OrderItem, OrderStatus
from fastapi.middleware.cors import CORSMiddleware
import os, requests
from jose import jwt
from typing import Optional, List
from bson.objectid import ObjectId
from fastapi.responses import JSONResponse
from datetime import datetime
from decimal import Decimal

app = FastAPI(
    title="Order Service",
    description="Service for managing confectionery orders",
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
db = client.get_database('confectionery').get_collection('orders')
SECRET = os.getenv('SECRET', 'your_jwt_secret')
CATALOG_URL = os.getenv('CATALOG_URL', 'http://catalog:8000')

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

@app.post('/orders', response_model=Order)
async def create_order(order: Order, user: dict = Depends(verify_token)):
    """
    Create a new order. Only users can create orders.
    """
    if user.get('role') != 'user':
        raise HTTPException(403, 'Only users can create orders')

    total = Decimal('0')
    
    try:
        # Fetch product details and calculate total
        for item in order.items:
            try:
                response = requests.get(f"{CATALOG_URL}/products/{item.product_id}")
                if response.status_code == 404:
                    raise HTTPException(400, f'Product {item.product_id} not found')
                elif response.status_code != 200:
                    raise HTTPException(500, 'Error fetching product information')
                
                product = response.json()
                item.product_name = product['name']
                item.unit_price = Decimal(str(product['price']))
                item.total_price = item.unit_price * item.quantity
                total += item.total_price
            except requests.RequestException as e:
                raise HTTPException(500, f'Error communicating with catalog service: {str(e)}')
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(500, f'Unexpected error: {str(e)}')
    
    order_data = {
        'user_id': user['sub'],
        'user_email': user['email'],
        'items': [
            {
                "product_id": item.product_id,
                "product_name": item.product_name,
                "quantity": item.quantity,
                "unit_price": float(item.unit_price),
                "total_price": float(item.total_price)
            } for item in order.items
        ],
        'total': float(total),
        'status': OrderStatus.PENDING.value,
        'created_at': datetime.now(),
        'updated_at': datetime.now(),
        'notes': order.notes,
        'delivery_address': order.delivery_address
    }

    try:
        result = await db.insert_one(order_data)
        order_data['id'] = str(result.inserted_id)
        return JSONResponse(content=order_data)
    except Exception as e:
        raise HTTPException(500, f'Error saving order: {str(e)}')

@app.get('/orders', response_model=List[Order])
async def list_orders(
    user: dict = Depends(verify_token),
    skip: int = Query(0, ge=0, description="Number of orders to skip"),
    limit: int = Query(10, ge=1, le=100, description="Number of orders to return"),
    status: Optional[OrderStatus] = Query(None, description="Filter by order status"),
    from_date: Optional[datetime] = Query(None, description="Filter orders from this date"),
    to_date: Optional[datetime] = Query(None, description="Filter orders until this date"),
    min_total: Optional[float] = Query(None, ge=0, description="Minimum order total"),
    max_total: Optional[float] = Query(None, gt=0, description="Maximum order total")
):
    """
    List orders with pagination and filtering options.
    Users can only see their own orders, while sellers can see all orders.
    """
    query = {}
    
    # Role-based filtering
    if user.get('role') == 'user':
        query['user_id'] = user['sub']
    elif user.get('role') != 'seller':
        raise HTTPException(403, 'Unauthorized')
    
    # Apply filters
    if status:
        query['status'] = status.value
    
    if from_date or to_date:
        query['created_at'] = {}
        if from_date:
            query['created_at']['$gte'] = from_date
        if to_date:
            query['created_at']['$lte'] = to_date
    
    if min_total is not None or max_total is not None:
        query['total'] = {}
        if min_total is not None:
            query['total']['$gte'] = min_total
        if max_total is not None:
            query['total']['$lte'] = max_total
    
    try:
        # Get total count for pagination
        total = await db.count_documents(query)
        
        # Get paginated results
        cursor = db.find(query).sort('created_at', -1).skip(skip).limit(limit)
        orders = await cursor.to_list(length=limit)
        
        # Transform orders
        for order in orders:
            order['id'] = str(order.pop('_id'))
        
        return JSONResponse(content={
            "total": total,
            "skip": skip,
            "limit": limit,
            "orders": orders
        })
    except Exception as e:
        raise HTTPException(500, f'Error retrieving orders: {str(e)}')

@app.get('/orders/{order_id}', response_model=Order)
async def get_order(order_id: str, user: dict = Depends(verify_token)):
    """
    Get a single order by ID.
    Users can only see their own orders, while sellers can see all orders.
    """
    try:
        order = await db.find_one({'_id': parse_object_id(order_id)})
        if not order:
            raise HTTPException(404, 'Order not found')
        
        # Check authorization
        if user.get('role') == 'user' and order['user_id'] != user['sub']:
            raise HTTPException(403, 'Access denied')
        elif user.get('role') not in ['user', 'seller']:
            raise HTTPException(403, 'Unauthorized')
        
        order['id'] = str(order.pop('_id'))
        return JSONResponse(content=order)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f'Error retrieving order: {str(e)}')

@app.put('/orders/{order_id}/status', response_model=Order)
async def update_order_status(
    order_id: str,
    status: OrderStatus,
    user: dict = Depends(verify_token)
):
    """
    Update order status. Only sellers can update order status.
    """
    if user.get('role') != 'seller':
        raise HTTPException(403, 'Only sellers can update order status')
    
    try:
        result = await db.update_one(
            {'_id': parse_object_id(order_id)},
            {
                '$set': {
                    'status': status.value,
                    'updated_at': datetime.now()
                }
            }
        )
        
        if result.modified_count == 0:
            raise HTTPException(404, 'Order not found')
        
        updated_order = await db.find_one({'_id': parse_object_id(order_id)})
        updated_order['id'] = str(updated_order.pop('_id'))
        return JSONResponse(content=updated_order)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f'Error updating order status: {str(e)}')

@app.put('/orders/{order_id}/cancel', response_model=Order)
async def cancel_order(order_id: str, user: dict = Depends(verify_token)):
    """
    Cancel an order. Users can only cancel their own pending orders.
    Sellers can cancel any pending order.
    """
    try:
        order = await db.find_one({'_id': parse_object_id(order_id)})
        if not order:
            raise HTTPException(404, 'Order not found')
        
        # Check authorization
        if user.get('role') == 'user':
            if order['user_id'] != user['sub']:
                raise HTTPException(403, 'Access denied')
        elif user.get('role') != 'seller':
            raise HTTPException(403, 'Unauthorized')
        
        # Check if order can be cancelled
        if order['status'] != OrderStatus.PENDING.value:
            raise HTTPException(400, 'Only pending orders can be cancelled')
        
        # Update order status
        result = await db.update_one(
            {'_id': parse_object_id(order_id)},
            {
                '$set': {
                    'status': OrderStatus.CANCELLED.value,
                    'updated_at': datetime.now()
                }
            }
        )
        
        updated_order = await db.find_one({'_id': parse_object_id(order_id)})
        updated_order['id'] = str(updated_order.pop('_id'))
        return JSONResponse(content=updated_order)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f'Error cancelling order: {str(e)}')

@app.get('/orders/stats/summary')
async def get_order_stats(
    user: dict = Depends(verify_token),
    from_date: Optional[datetime] = Query(None, description="Start date for statistics"),
    to_date: Optional[datetime] = Query(None, description="End date for statistics")
):
    """
    Get order statistics. Users can only see their own stats, while sellers can see all stats.
    """
    try:
        match = {}
        
        # Role-based filtering
        if user.get('role') == 'user':
            match['user_id'] = user['sub']
        elif user.get('role') != 'seller':
            raise HTTPException(403, 'Unauthorized')
        
        # Date filtering
        if from_date or to_date:
            match['created_at'] = {}
            if from_date:
                match['created_at']['$gte'] = from_date
            if to_date:
                match['created_at']['$lte'] = to_date
        
        pipeline = [
            {'$match': match},
            {
                '$group': {
                    '_id': '$status',
                    'count': {'$sum': 1},
                    'total_amount': {'$sum': '$total'}
                }
            }
        ]
        
        stats = await db.aggregate(pipeline).to_list(None)
        
        # Transform stats into a more readable format
        result = {
            'total_orders': 0,
            'total_amount': 0,
            'by_status': {}
        }
        
        for stat in stats:
            status = stat['_id']
            count = stat['count']
            amount = stat['total_amount']
            
            result['total_orders'] += count
            result['total_amount'] += amount
            result['by_status'][status] = {
                'count': count,
                'total_amount': amount
            }
        
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(500, f'Error retrieving order statistics: {str(e)}')
