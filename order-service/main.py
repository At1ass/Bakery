from fastapi import FastAPI, Depends, HTTPException, Header
from motor.motor_asyncio import AsyncIOMotorClient
from models import Order, OrderItem
from fastapi.middleware.cors import CORSMiddleware
import os, requests
from jose import jwt
from typing import Optional, List
from bson.objectid import ObjectId

app = FastAPI()

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
SECRET = os.getenv('SECRET', 'your_jwt_secret')  # Add default secret for development

async def verify_token(authorization: Optional[str] = Header(None)) -> dict:
    if not authorization:
        raise HTTPException(401, 'Authorization required')
    try:
        token = authorization.split(' ')[1]
        payload = jwt.decode(token, SECRET, algorithms=['HS256'])
        return payload
    except:
        raise HTTPException(401, 'Invalid token')

@app.post('/orders')
async def create_order(order: Order, user: dict = Depends(verify_token)):
    if user.get('role') != 'user':
        raise HTTPException(403, 'Only users can create orders')

    if not order.items:
        raise HTTPException(400, 'Order must contain at least one item')

    total = 0
    try:
        for item in order.items:
            response = requests.get(f"http://catalog:8000/products/{item.product_id}")
            if response.status_code == 404:
                raise HTTPException(400, f'Product {item.product_id} not found')
            elif response.status_code != 200:
                raise HTTPException(500, 'Error fetching product information')
            
            product = response.json()
            total += product['price'] * item.quantity
    except requests.RequestException:
        raise HTTPException(500, 'Error communicating with catalog service')
    
    order_data = {
        'user_id': user['sub'],
        'user_email': user['email'],
        'items': [item.dict() for item in order.items],
        'total': total,
        'status': 'pending',
        'created_at': order.created_at
    }

    result = await db.insert_one(order_data)
    order_data['id'] = str(result.inserted_id)
    return order_data

@app.get('/orders')
async def list_orders(user: dict = Depends(verify_token)):
    if user.get('role') == 'user':
        # Users can only see their own orders
        cursor = db.find({'user_id': user['sub']})
    elif user.get('role') == 'seller':
        # Sellers can see all orders
        cursor = db.find()
    else:
        raise HTTPException(403, 'Unauthorized')
    
    orders = await cursor.to_list(100)
    for order in orders:
        order['id'] = str(order['_id'])
        del order['_id']
    return orders
