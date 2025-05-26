from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
from models import UserIn, UserOut, Token, TokenData
import os, bcrypt, logging, re, asyncio
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from passlib.context import CryptContext

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Password hashing configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Initialize FastAPI app with documentation settings
app = FastAPI(
    title="Auth Service",
    description="Authentication service for the confectionery store",
    version="1.0.0",
    docs_url=None if os.getenv('ENVIRONMENT') == 'production' else "/docs",
    redoc_url=None if os.getenv('ENVIRONMENT') == 'production' else "/redoc"
)

# Rate limiting configuration with more restrictive limits
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS configuration with specific origins and security headers
ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', 'http://localhost:3000,http://localhost:3001').split(',')
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
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
users_collection = None

async def init_db():
    global db, users_collection
    
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
        users_collection = db.get_collection('users')
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

@app.on_event("startup")
async def startup_event():
    await init_db()

# Security configuration with strong defaults
SECRET = os.getenv('SECRET')
if not SECRET or len(SECRET) < 32:
    logger.error("Insecure or missing SECRET key")
    raise ValueError("SECRET key must be at least 32 characters long")

ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', '30'))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv('REFRESH_TOKEN_EXPIRE_DAYS', '7'))
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='login')

# Password validation with stronger requirements
MIN_PASSWORD_LENGTH = 12
PASSWORD_PATTERN = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{12,}$'

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error(f"Password verification failed: {e}")
        return False

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })
    try:
        return jwt.encode(to_encode, SECRET, algorithm=ALGORITHM)
    except Exception as e:
        logger.error(f"Token creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create access token"
        )

def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    })
    try:
        return jwt.encode(to_encode, SECRET, algorithm=ALGORITHM)
    except Exception as e:
        logger.error(f"Refresh token creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create refresh token"
        )

@app.post('/register', response_model=UserOut, status_code=status.HTTP_201_CREATED)
@limiter.limit("3/minute")
async def register(user: UserIn):
    try:
        # Validate password strength
        if len(user.password) < MIN_PASSWORD_LENGTH:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Password must be at least {MIN_PASSWORD_LENGTH} characters long"
            )

        if not re.match(PASSWORD_PATTERN, user.password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must contain uppercase, lowercase, number, and special character"
            )

        # Check if user exists with case-insensitive email comparison
        existing_user = await users_collection.find_one({
            'email': {'$regex': f'^{user.email}$', '$options': 'i'}
        })
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered"
            )
        
        # Hash password and create user
        hashed_password = get_password_hash(user.password)
        doc = {
            'email': user.email.lower(),  # Store email in lowercase
            'hashed_password': hashed_password,
            'role': user.role,
            'created_at': datetime.utcnow(),
            'last_login': None,
            'failed_login_attempts': 0,
            'locked_until': None
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
        user = await users_collection.find_one({'email': form_data.username.lower()})
        
        # Check if account is locked
        if user and user.get('locked_until'):
            if datetime.utcnow() < user['locked_until']:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Account is temporarily locked. Try again later.",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            else:
                # Reset lock if expired
                await users_collection.update_one(
                    {'_id': user['_id']},
                    {'$set': {'locked_until': None, 'failed_login_attempts': 0}}
                )

        if not user or not verify_password(form_data.password, user['hashed_password']):
            if user:
                # Increment failed login attempts
                failed_attempts = user.get('failed_login_attempts', 0) + 1
                update = {
                    '$set': {
                        'failed_login_attempts': failed_attempts
                    }
                }
                
                # Lock account after 5 failed attempts
                if failed_attempts >= 5:
                    lock_until = datetime.utcnow() + timedelta(minutes=15)
                    update['$set']['locked_until'] = lock_until
                
                await users_collection.update_one({'_id': user['_id']}, update)
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Reset failed attempts and update last login
        await users_collection.update_one(
            {'_id': user['_id']},
            {
                '$set': {
                    'failed_login_attempts': 0,
                    'last_login': datetime.utcnow(),
                    'locked_until': None
                }
            }
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
        
        refresh_token = create_refresh_token(
            data={
                "sub": str(user['_id']),
                "email": user['email']
            }
        )
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
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

@app.post('/refresh', response_model=Token)
async def refresh_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token type"
            )
        
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        from bson.objectid import ObjectId
        user = await users_collection.find_one({'_id': ObjectId(user_id)})
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token = create_access_token(
            data={
                "sub": str(user['_id']),
                "email": user['email'],
                "role": user['role']
            },
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        
        new_refresh_token = create_refresh_token(
            data={
                "sub": str(user['_id']),
                "email": user['email']
            }
        )
        
        return Token(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            role=user['role']
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET, algorithms=[ALGORITHM])
        if payload.get("type") != "access":
            raise credentials_exception
        
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
        await db.command('ping')
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service unhealthy"
        )
