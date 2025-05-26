# Auth Service

A modern, secure authentication and authorization microservice built with FastAPI, following best practices for enterprise-grade applications.

## 🏗️ Architecture

This service follows a clean, layered architecture with clear separation of concerns:

```
auth-service/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── core/                   # Core functionality
│   │   ├── __init__.py
│   │   ├── config.py          # Configuration management
│   │   ├── security.py        # Security utilities (JWT, passwords)
│   │   └── logging.py         # Logging configuration
│   ├── models/                 # Pydantic models
│   │   ├── __init__.py
│   │   ├── user.py            # User data models
│   │   └── token.py           # Token data models
│   ├── database/               # Database layer
│   │   ├── __init__.py
│   │   ├── connection.py      # Database connection management
│   │   └── repositories.py    # Repository pattern implementation
│   ├── services/               # Business logic
│   │   ├── __init__.py
│   │   └── auth_service.py    # Authentication business logic
│   └── api/                    # API layer
│       ├── __init__.py
│       ├── dependencies.py    # FastAPI dependencies
│       └── routers/           # API route handlers
│           ├── __init__.py
│           ├── auth.py        # Authentication endpoints
│           └── users.py       # User management endpoints
├── Dockerfile
├── requirements.txt
└── README.md
```

## ✨ Features

### Security
- **JWT Authentication**: Secure token-based authentication with access and refresh tokens
- **Password Security**: Strong password requirements with bcrypt hashing
- **Rate Limiting**: Configurable rate limits for all endpoints
- **Account Locking**: Automatic account locking after failed login attempts
- **Security Headers**: Comprehensive security headers for production use

### Configuration
- **Environment-based**: All configuration through environment variables
- **Validation**: Pydantic-based configuration validation
- **Flexible**: Support for development, testing, and production environments

### Database
- **MongoDB**: Async MongoDB integration with Motor
- **Connection Pooling**: Optimized connection management
- **Retry Logic**: Robust error handling and retry mechanisms
- **Indexing**: Automatic index creation for performance

### API Design
- **OpenAPI**: Automatic API documentation generation
- **Type Safety**: Full type hints and validation
- **Error Handling**: Comprehensive error responses
- **CORS**: Configurable CORS support

## 🚀 Quick Start

### Environment Variables

Create a `.env` file with the following variables:

```bash
# Required
AUTH_JWT_SECRET="your-super-secret-jwt-key-at-least-32-characters-long"

# Optional (with defaults)
AUTH_ENVIRONMENT="development"
AUTH_DEBUG=true
AUTH_MONGO_URI="mongodb://mongo:27017"
AUTH_ALLOWED_ORIGINS="http://localhost:3001,https://localhost:3002"
```

### Running with Docker

```bash
# Build the image
docker build -t auth-service .

# Run the container
docker run -d \
  -p 8001:8000 \
  -e AUTH_JWT_SECRET="your-secret-key" \
  --name auth-service \
  auth-service
```

### Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export AUTH_JWT_SECRET="your-secret-key"

# Run the application
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## 📚 API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## 🔐 Authentication Flow

### 1. User Registration
```bash
POST /auth/register
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "role": "Customer"
}
```

### 2. User Login
```bash
POST /auth/login
{
  "username": "user@example.com",
  "password": "SecurePass123!"
}
```

Response:
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "role": "Customer",
  "expires_in": 1800
}
```

### 3. Token Refresh
```bash
POST /auth/refresh
{
  "refresh_token": "eyJ..."
}
```

### 4. Protected Endpoints
Include the access token in the Authorization header:
```bash
Authorization: Bearer eyJ...
```

## 🛡️ Security Features

### Password Requirements
- Minimum 12 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one number
- At least one special character (@$!%*?&)

### Rate Limiting
- Login: 5 attempts per minute
- Registration: 3 attempts per minute
- Token refresh: 5 attempts per minute

### Account Security
- Account locked for 30 minutes after 5 failed login attempts
- JWT tokens include unique IDs for revocation capability
- Secure password hashing with bcrypt

## 🔧 Configuration

All configuration is handled through environment variables with the `AUTH_` prefix:

| Variable | Default | Description |
|----------|---------|-------------|
| `AUTH_JWT_SECRET` | **Required** | JWT signing secret (min 32 chars) |
| `AUTH_ENVIRONMENT` | `development` | Environment (development/production/testing) |
| `AUTH_DEBUG` | `false` | Enable debug mode |
| `AUTH_MONGO_URI` | `mongodb://mongo:27017` | MongoDB connection string |
| `AUTH_ALLOWED_ORIGINS` | `http://localhost:3001,https://localhost:3002` | CORS allowed origins |

## 🏥 Health Checks

- **Health endpoint**: `GET /health`
- **Docker health check**: Built-in container health monitoring
- **Database connectivity**: Automatic database connection verification

## 🧪 Testing

```bash
# Run tests (when implemented)
pytest

# Check code quality
flake8 app/
black app/
mypy app/
```

## 📈 Monitoring

The service includes:
- Structured logging with configurable levels
- Health check endpoints
- Request/response logging
- Error tracking and reporting

## 🔄 Development

### Code Structure Guidelines
- **Separation of Concerns**: Each layer has a specific responsibility
- **Dependency Injection**: Services are injected through FastAPI dependencies
- **Type Safety**: Full type hints throughout the codebase
- **Error Handling**: Comprehensive exception handling
- **Documentation**: Docstrings for all public methods

### Adding New Features
1. Add models in `app/models/`
2. Implement business logic in `app/services/`
3. Create database operations in `app/database/repositories.py`
4. Add API endpoints in `app/api/routers/`
5. Update configuration in `app/core/config.py` if needed

## 🚀 Production Deployment

### Environment Variables for Production
```bash
AUTH_ENVIRONMENT=production
AUTH_DEBUG=false
AUTH_JWT_SECRET="your-production-secret-key"
AUTH_MONGO_URI="mongodb://your-production-mongo:27017"
AUTH_ALLOWED_ORIGINS="https://your-domain.com"
```

### Security Considerations
- Use strong, unique JWT secrets
- Enable HTTPS in production
- Configure proper CORS origins
- Monitor rate limiting and failed login attempts
- Regular security updates

## 📄 License

This project is part of the Mimikurs confectionery e-commerce platform. 