from fastapi import FastAPI, HTTPException, Depends, Header
from motor.motor_asyncio import AsyncIOMotorClient
from models import Product
from fastapi.middleware.cors import CORSMiddleware
import os
from jose import jwt
from typing import Optional
from bson.objectid import ObjectId
from fastapi.encoders import jsonable_encoder
import json

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
db = client.get_database('confectionery').get_collection('products')
SECRET = os.getenv('SECRET', 'your_jwt_secret')  # Add default secret for development

class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return super().default(o)

async def verify_token(authorization: Optional[str] = Header(None)) -> dict:
    if not authorization:
        return {'role': None}
    try:
        token = authorization.split(' ')[1]
        payload = jwt.decode(token, SECRET, algorithms=['HS256'])
        return payload
    except:
        return {'role': None}

@app.get('/products')
async def list_products():
    cursor = db.find()
    products = await cursor.to_list(100)
    for product in products:
        product['id'] = str(product['_id'])
        del product['_id']  # Remove the MongoDB _id
    return products

@app.get('/products/{product_id}')
async def get_product(product_id: str):
    try:
        product = await db.find_one({'_id': ObjectId(product_id)})
        if not product:
            raise HTTPException(404, 'Product not found')
        product['id'] = str(product['_id'])
        del product['_id']
        return product
    except:
        raise HTTPException(404, 'Product not found')

@app.post('/products')
async def create_product(product: Product, user: dict = Depends(verify_token)):
    if user.get('role') != 'seller':
        raise HTTPException(403, 'Only sellers can create products')
    
    # Convert the product to dict and ensure recipe is a list
    product_dict = product.dict(exclude={'id'})
    if 'recipe' not in product_dict or product_dict['recipe'] is None:
        product_dict['recipe'] = []
    
    # Insert into MongoDB
    result = await db.insert_one(product_dict)
    
    # Return the created product with id
    created_product = {
        'id': str(result.inserted_id),
        **product_dict
    }
    return created_product

@app.put('/products/{product_id}')
async def update_product(product_id: str, product: Product, user: dict = Depends(verify_token)):
    if user.get('role') != 'seller':
        raise HTTPException(403, 'Only sellers can update products')
    
    # Convert the product to dict and ensure recipe is a list
    product_dict = product.dict(exclude={'id'})
    if 'recipe' not in product_dict or product_dict['recipe'] is None:
        product_dict['recipe'] = []
    
    # Update in MongoDB
    await db.update_one(
        {'_id': ObjectId(product_id)},
        {'$set': product_dict}
    )
    
    # Return the updated product
    updated_product = {
        'id': product_id,
        **product_dict
    }
    return updated_product

@app.delete('/products/{product_id}')
async def delete_product(product_id: str, user: dict = Depends(verify_token)):
    if user.get('role') != 'seller':
        raise HTTPException(403, 'Only sellers can delete products')
    
    await db.delete_one({'_id': ObjectId(product_id)})
    return {'message': 'Product deleted successfully'}
