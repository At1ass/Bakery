from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from motor.motor_asyncio import AsyncIOMotorClient
from jose import JWTError, jwt
from models import UserIn, UserOut, Token
import os, bcrypt
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Add CORS middleware with specific origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Connect to MongoDB with explicit database name
MONGO_URL = os.getenv('MONGO', 'mongodb://mongo:27017/confectionery')
client = AsyncIOMotorClient(MONGO_URL)
db = client.get_database('confectionery').get_collection('users')
SECRET = os.getenv('SECRET', 'your_jwt_secret')  # Add default secret for development
ALGORITHM = 'HS256'
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='login')

@app.post('/register', response_model=UserOut)
async def register(user: UserIn):
    # Check if user already exists
    existing_user = await db.find_one({'email': user.email})
    if existing_user:
        raise HTTPException(400, 'Email already registered')
    
    hashed = bcrypt.hashpw(user.password.encode(), bcrypt.gensalt())
    doc = {
        'email': user.email,
        'password': hashed,
        'role': user.role
    }
    res = await db.insert_one(doc)
    return UserOut(id=str(res.inserted_id), email=user.email, role=user.role)

@app.post('/login', response_model=Token)
async def login(form: OAuth2PasswordRequestForm = Depends()):
    user = await db.find_one({'email': form.username})
    if not user or not bcrypt.checkpw(form.password.encode(), user['password']):
        raise HTTPException(401, 'Invalid credentials')
    
    token = jwt.encode(
        {
            'sub': str(user['_id']),
            'email': user['email'],
            'role': user['role']
        },
        SECRET,
        algorithm=ALGORITHM
    )
    return Token(access_token=token, token_type='bearer', role=user['role'])

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET, algorithms=[ALGORITHM])
        uid = payload.get('sub')
        if not uid:
            raise HTTPException(401, 'Invalid token')
    except JWTError:
        raise HTTPException(401, 'Invalid token')
    
    from bson.objectid import ObjectId
    user = await db.find_one({'_id': ObjectId(uid)})
    if not user:
        raise HTTPException(401, 'User not found')
    return user

@app.get('/me', response_model=UserOut)
async def get_me(current_user: dict = Depends(get_current_user)):
    return UserOut(
        id=str(current_user['_id']),
        email=current_user['email'],
        role=current_user['role']
    )
