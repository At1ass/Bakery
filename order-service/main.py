from fastapi import FastAPI, Depends, HTTPException, Header
from motor.motor_asyncio import AsyncIOMotorClient
from models import Order, OrderItem
from fastapi.middleware.cors import CORSMiddleware
import os, requests
from jose import jwt
from typing import Optional, List
from bson.objectid import ObjectId
from fastapi.responses import JSONResponse

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

    total = 0
    catalog_url = os.getenv('CATALOG_URL', 'http://catalog:8000')
    
    try:
        for item in order.items:
            try:
                response = requests.get(f"{catalog_url}/products/{item.product_id}")
                if response.status_code == 404:
                    raise HTTPException(400, f'Product {item.product_id} not found')
                elif response.status_code != 200:
                    raise HTTPException(500, 'Error fetching product information')
                
                product = response.json()
                total += float(product['price']) * item.quantity
            except requests.RequestException as e:
                raise HTTPException(500, f'Error communicating with catalog service: {str(e)}')
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(500, f'Unexpected error: {str(e)}')
    
    order_data = {
        'user_id': user['sub'],
        'user_email': user['email'],
        'items': [{"product_id": item.product_id, "quantity": item.quantity} for item in order.items],
        'total': total,
        'status': 'pending',
        'created_at': order.created_at
    }

    try:
        result = await db.insert_one(order_data)
        order_data['id'] = str(result.inserted_id)
        return JSONResponse(content=order_data)
    except Exception as e:
        raise HTTPException(500, f'Error saving order: {str(e)}')

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
    
    try:
        orders = await cursor.to_list(100)
        for order in orders:
            order['id'] = str(order['_id'])
            del order['_id']
        return JSONResponse(content=orders)
    except Exception as e:
        raise HTTPException(500, f'Error retrieving orders: {str(e)}')
