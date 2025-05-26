from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
from models import UserIn, UserOut, Token, TokenData
import os, bcrypt, logging
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app with documentation settings
app = FastAPI(
    title="Auth Service",
    description="Authentication service for the confectionery store",
    version="1.0.0"
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
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Database configuration
MONGO_URL = os.getenv('MONGO', 'mongodb://mongo:27017/confectionery')
try:
    client = AsyncIOMotorClient(MONGO_URL)
    db = client.get_database('confectionery')
    users_collection = db.get_collection('users')
except Exception as e:
    logger.error(f"Failed to connect to database: {e}")
    raise

# Security configuration
SECRET = os.getenv('SECRET')
if not SECRET:
    logger.error("No SECRET key provided")
    raise ValueError("SECRET key is required")

ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', '30'))
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='login')

# Password validation
MIN_PASSWORD_LENGTH = 8

def verify_password(plain_password: str, hashed_password: bytes) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode(), hashed_password)
    except Exception as e:
        logger.error(f"Password verification failed: {e}")
        return False

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    try:
        return jwt.encode(to_encode, SECRET, algorithm=ALGORITHM)
    except Exception as e:
        logger.error(f"Token creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create access token"
        )

@app.post('/register', response_model=UserOut, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register(user: UserIn):
    try:
        # Validate password strength
        if len(user.password) < MIN_PASSWORD_LENGTH:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Password must be at least {MIN_PASSWORD_LENGTH} characters long"
            )

        # Check if user exists
        existing_user = await users_collection.find_one({'email': user.email})
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered"
            )
        
        # Hash password and create user
        hashed = bcrypt.hashpw(user.password.encode(), bcrypt.gensalt())
        doc = {
            'email': user.email,
            'password': hashed,
            'role': user.role,
            'created_at': datetime.utcnow()
        }
        result = await users_collection.insert_one(doc)
        
        return UserOut(id=str(result.inserted_id), email=user.email, role=user.role)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )

@app.post('/login', response_model=Token)
@limiter.limit("5/minute")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        user = await users_collection.find_one({'email': form_data.username})
        if not user or not verify_password(form_data.password, user['password']):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={
                "sub": str(user['_id']),
                "email": user['email'],
                "role": user['role']
            },
            expires_delta=access_token_expires
        )
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            role=user['role']
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET, algorithms=[ALGORITHM])
        uid: str = payload.get("sub")
        if uid is None:
            raise credentials_exception
        token_data = TokenData(uid=uid)
    except JWTError:
        raise credentials_exception
    
    try:
        from bson.objectid import ObjectId
        user = await users_collection.find_one({'_id': ObjectId(token_data.uid)})
        if user is None:
            raise credentials_exception
        return user
    except Exception as e:
        logger.error(f"User retrieval failed: {e}")
        raise credentials_exception

@app.get('/me', response_model=UserOut)
async def get_me(current_user: dict = Depends(get_current_user)):
    try:
        return UserOut(
            id=str(current_user['_id']),
            email=current_user['email'],
            role=current_user['role']
        )
    except Exception as e:
        logger.error(f"Profile retrieval failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not retrieve user profile"
        )

@app.get("/health")
async def health_check():
    try:
        # Check database connection
        await client.admin.command('ping')
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service unhealthy"
        )
