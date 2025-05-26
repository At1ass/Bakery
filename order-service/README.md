# Order Service

A FastAPI-based microservice for managing orders in the confectionery system.

## Architecture

The service follows FastAPI best practices with a clean, modular architecture:

```
order-service/
├── app/
│   ├── api/                    # API layer
│   │   ├── dependencies.py     # Common dependencies
│   │   └── routers/           # API route handlers
│   │       ├── orders.py      # Order management endpoints
│   │       └── health.py      # Health check endpoints
│   ├── core/                  # Core configuration
│   │   ├── config.py          # Application settings
│   │   └── security.py        # JWT authentication
│   ├── db/                    # Database layer
│   │   └── mongodb.py         # MongoDB connection & operations
│   ├── models/                # Data models
│   │   └── order.py           # Order Pydantic models
│   ├── schemas/               # Response schemas
│   │   └── order.py           # API response models
│   ├── services/              # Business logic
│   │   ├── external.py        # External service communication
│   │   └── order_service.py   # Order business logic
│   └── main.py                # FastAPI application
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Container configuration
└── README.md                  # This file
```

## Features

### Order Management
- **Create Orders**: Validate products and calculate totals automatically
- **List Orders**: Paginated order listing with filtering options
- **Get Order**: Retrieve specific order details
- **Update Status**: Manage order lifecycle with validation
- **Cancel Orders**: Cancel orders with business rule validation

### Security
- JWT token authentication
- User-specific order access control
- Input validation and sanitization

### External Integrations
- **Auth Service**: User authentication and authorization
- **Catalog Service**: Product validation and pricing

### Monitoring & Health
- Health check endpoints for container orchestration
- Comprehensive logging with structured format
- Request timing middleware
- Database connection monitoring

## API Endpoints

### Orders
- `POST /api/v1/orders/` - Create a new order
- `GET /api/v1/orders/` - List user orders (with pagination and filtering)
- `GET /api/v1/orders/{order_id}` - Get specific order
- `PATCH /api/v1/orders/{order_id}/status` - Update order status
- `DELETE /api/v1/orders/{order_id}/cancel` - Cancel order

### Health & Monitoring
- `GET /api/v1/health/` - Health check with database connectivity
- `GET /api/v1/health/ready` - Readiness probe for Kubernetes
- `GET /api/v1/health/live` - Liveness probe for Kubernetes

### Documentation
- `GET /docs` - Interactive API documentation (Swagger UI)
- `GET /redoc` - Alternative API documentation (ReDoc)

## Configuration

The service uses environment variables for configuration:

### Application Settings
- `APP_NAME` - Application name (default: "Order Service")
- `APP_VERSION` - Application version (default: "1.0.0")
- `ENVIRONMENT` - Environment (development/production)
- `DEBUG` - Debug mode (default: False)

### Database
- `MONGO` - MongoDB connection URL
- `DATABASE_NAME` - Database name (default: "confectionery")

### Security
- `JWT_SECRET` - JWT signing secret (required)
- `JWT_ALGORITHM` - JWT algorithm (default: "HS256")

### External Services
- `AUTH_SERVICE_URL` - Authentication service URL
- `CATALOG_SERVICE_URL` - Catalog service URL

### CORS & Security
- `ALLOWED_ORIGINS` - Comma-separated list of allowed origins

## Order Status Workflow

The service implements a state machine for order status transitions:

```
pending → confirmed → preparing → ready → completed
   ↓         ↓          ↓
cancelled  cancelled  cancelled
```

Valid transitions:
- `pending` → `confirmed`, `cancelled`
- `confirmed` → `preparing`, `cancelled`
- `preparing` → `ready`, `cancelled`
- `ready` → `completed`
- `completed` → (final state)
- `cancelled` → (final state)

## Development

### Running Locally
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export MONGO=mongodb://localhost:27017
export JWT_SECRET=your-secret-key
export AUTH_SERVICE_URL=http://localhost:8001
export CATALOG_SERVICE_URL=http://localhost:8002

# Run the application
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Docker
```bash
# Build the image
docker build -t order-service .

# Run the container
docker run -p 8000:8000 \
  -e MONGO=mongodb://mongo:27017 \
  -e JWT_SECRET=your-secret-key \
  order-service
``` 