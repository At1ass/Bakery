# Confectionery E-commerce Microservice System

A secure, containerized microservice-based e-commerce platform for confectionery products with multi-language support.

## 🌐 Internationalization (i18n)

The application supports multiple languages:
- **English** (default)
- **Russian** (Русский)

### Language Features
- **Automatic Detection**: Uses browser language or saved preference
- **Persistent Selection**: Language choice is saved in localStorage
- **Complete Translation**: All UI elements, messages, and forms are translated
- **Easy Switching**: Language switcher in the header for instant switching

### Supported Languages
- 🇺🇸 **English**: Complete interface in English
- 🇷🇺 **Russian**: Полный интерфейс на русском языке

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- mkcert (for SSL certificates)

### SSL Certificate Setup

1. **Install mkcert**:
   ```bash
   # Manjaro/Arch Linux
   sudo pacman -S mkcert
   
   # Ubuntu/Debian
   sudo apt install libnss3-tools
   curl -JLO "https://dl.filippo.io/mkcert/latest?for=linux/amd64"
   chmod +x mkcert-v*-linux-amd64
   sudo mv mkcert-v*-linux-amd64 /usr/local/bin/mkcert
   
   # macOS
   brew install mkcert
   ```

2. **Install the root CA**:
   ```bash
   mkcert -install
   ```

3. **Generate certificates** (already done in this project):
   ```bash
   mkdir ssl-certs
   cd ssl-certs
   mkcert localhost 127.0.0.1 ::1
   ```

### Running the Application

1. **Start all services**:
   ```bash
   docker-compose up -d
   ```

2. **Access the application**:
   - **HTTPS (Secure)**: https://localhost:3002
   - **HTTP (Redirects to HTTPS)**: http://localhost:3001

3. **Check service status**:
   ```bash
   docker-compose ps
   ```

## 🏗️ Architecture

### Services

- **Frontend**: React.js application with Nginx (HTTPS)
- **Auth Service**: User authentication and authorization
- **Catalog Service**: Product catalog management
- **Order Service**: Order processing and management
- **MongoDB**: Database for all services

### Ports

- `3001`: HTTP (redirects to HTTPS)
- `3002`: HTTPS (main application)
- `8001`: Auth Service API
- `8002`: Catalog Service API
- `8003`: Order Service API
- `27017`: MongoDB

## 🔐 Security Features

- ✅ **HTTPS/TLS 1.3** with locally trusted certificates
- ✅ **bcrypt password hashing** (12 salt rounds)
- ✅ **JWT authentication** with secure tokens
- ✅ **Rate limiting** on API endpoints
- ✅ **Security headers** (HSTS, CSP, XSS protection)
- ✅ **CORS protection** with specific origins
- ✅ **Container security** with resource limits

## 🛠️ Development

### Environment Variables

Create a `.env` file:
```bash
JWT_SECRET=your-super-secret-jwt-key-here
MONGO_URI=mongodb://mongo:27017
```

### Building Services

```bash
# Build all services
docker-compose build

# Build specific service
docker-compose build frontend
```

### Logs

```bash
# View all logs
docker-compose logs

# View specific service logs
docker-compose logs frontend
docker-compose logs auth
```

## 📱 Usage

### Customer Flow

1. **Register/Login**: Create account or sign in
2. **Browse Products**: View available confectionery items
3. **Add to Cart**: Select products and quantities
4. **Place Order**: Provide delivery details and submit

### Seller Flow

1. **Login**: Sign in with seller credentials
2. **View Orders**: See incoming customer orders
3. **Update Status**: Mark orders as processing/shipped/delivered

## 🔧 Troubleshooting

### SSL Certificate Issues

If you see "Connection not secure" warnings:

1. **Check mkcert installation**:
   ```bash
   mkcert -install
   ```

2. **Restart your browser** after installing mkcert

3. **Clear browser cache** and try again

### Service Issues

```bash
# Restart all services
docker-compose restart

# View service health
docker-compose ps

# Check specific service logs
docker-compose logs [service-name]
```

## 📚 API Documentation

### Authentication Endpoints

- `POST /register` - User registration
- `POST /login` - User login
- `GET /profile` - Get user profile

### Catalog Endpoints

- `GET /products` - List all products
- `GET /products/{id}` - Get product details

### Order Endpoints

- `POST /orders` - Create new order
- `GET /orders` - List user orders
- `PUT /orders/{id}/status` - Update order status

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For issues and questions:
- Check the [Security Documentation](SECURITY.md)
- Review the troubleshooting section above
- Open an issue on GitHub 