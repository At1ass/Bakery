# 🍰 Mimikurs - Confectionery E-commerce Platform

A modern, multilingual e-commerce platform for confectionery businesses built with microservices architecture, featuring beautiful UI design, complete internationalization (English/Russian), and HTTPS support.

## ✨ Features

- **🏗️ Microservices Architecture**: Separate services for authentication, catalog, and orders
- **🌍 Internationalization**: Complete English and Russian translations
- **🔒 HTTPS Support**: SSL certificates with mkcert for secure local development
- **🎨 Modern UI**: Beautiful, responsive design inspired by modern e-commerce platforms
- **🐳 Docker Containerized**: Easy deployment with Docker Compose
- **📱 Mobile Responsive**: Works perfectly on all devices
- **🔐 JWT Authentication**: Secure user authentication with role-based access
- **🛒 Shopping Cart**: Real-time cart management with quantity controls
- **👨‍💼 Seller Dashboard**: Complete product and order management interface

## 🚀 Quick Start

### Automatic Installation

We provide automated installation scripts for all major platforms:

#### 🐧 Linux (Arch/Debian/RPM-based)

```bash
# Make the script executable
chmod +x install.sh

# Run the installer
./install.sh
```

#### 🪟 Windows

**Option 1: Using PowerShell (Recommended)**
```powershell
# Run PowerShell as Administrator, then:
.\install.ps1
```

**Option 2: Using Batch File**
```cmd
# Right-click install.bat and select "Run as administrator"
install.bat
```

### What the installer does:

1. **Detects your operating system** and installs appropriate packages
2. **Installs Docker** and Docker Compose if not present
3. **Installs mkcert** for SSL certificate generation
4. **Generates SSL certificates** for localhost
5. **Builds and starts** all microservices
6. **Provides access URLs** and default credentials

## 🛠️ Manual Installation

If you prefer manual installation or the automatic script doesn't work:

### Prerequisites

- **Docker** and **Docker Compose**
- **mkcert** for SSL certificates
- **Git** (for cloning the repository)

### Step 1: Install Dependencies

#### Linux (Ubuntu/Debian)
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install mkcert
wget -O mkcert https://github.com/FiloSottile/mkcert/releases/latest/download/mkcert-v1.4.4-linux-amd64
chmod +x mkcert
sudo mv mkcert /usr/local/bin/
```

#### Linux (Arch/Manjaro)
```bash
# Install Docker and mkcert
sudo pacman -S docker docker-compose mkcert

# Start Docker service
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER
```

#### Windows
```powershell
# Install Chocolatey (if not installed)
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Install Docker Desktop and mkcert
choco install docker-desktop mkcert -y
```

### Step 2: Generate SSL Certificates

```bash
# Create certificates directory
mkdir -p certs
cd certs

# Install local CA
mkcert -install

# Generate certificates for localhost
mkcert localhost 127.0.0.1 ::1

# Rename files for docker-compose
mv localhost+2.pem cert.pem
mv localhost+2-key.pem key.pem

cd ..
```

### Step 3: Start the Application

```bash
# Build and start all services
docker-compose up --build -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

## 🌐 Access the Application

After successful installation:

- **🌐 Frontend**: https://localhost:3002
- **🔧 Auth API**: http://localhost:8001
- **📦 Catalog API**: http://localhost:8002
- **🛒 Orders API**: http://localhost:8003

### Default Credentials

- **📧 Email**: `admin@mimikurs.com`
- **🔑 Password**: `admin123`

## 🏗️ Architecture

### Microservices

1. **Auth Service** (Port 8001)
   - User registration and authentication
   - JWT token management
   - Role-based access control

2. **Catalog Service** (Port 8002)
   - Product management
   - Category management
   - Inventory tracking

3. **Order Service** (Port 8003)
   - Shopping cart management
   - Order processing
   - Order history

4. **Frontend** (Port 3002)
   - React.js application
   - Responsive design
   - Internationalization support

5. **Database** (Port 27017)
   - MongoDB for data persistence
   - Separate collections for each service

## 🌍 Internationalization

The platform supports complete internationalization with:

- **English** (default)
- **Russian** (Русский)

### Language Features

- **379+ translation keys** covering all UI elements
- **Persistent language selection** using localStorage
- **Flag-based language switcher** (🇺🇸/🇷🇺)
- **Real-time language switching** without page reload

## 🎨 UI Design

Modern e-commerce design featuring:

- **Gradient backgrounds** and animations
- **Card-based layouts** with hover effects
- **Responsive grid systems**
- **Modern typography** with gradient text
- **Smooth transitions** and micro-interactions
- **Custom scrollbars** and loading states
- **Mobile-first responsive design**

## 🔧 Development

### Project Structure

```
mimikurs/
├── auth-service/          # Authentication microservice
├── catalog-service/       # Product catalog microservice
├── order-service/         # Order management microservice
├── frontend/             # React.js frontend application
├── certs/               # SSL certificates
├── docker-compose.yml   # Docker services configuration
├── install.sh          # Linux installation script
├── install.ps1         # Windows PowerShell script
├── install.bat         # Windows batch script
└── README.md           # This file
```

### Available Commands

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f [service-name]

# Rebuild specific service
docker-compose up --build [service-name]

# Scale services
docker-compose up --scale catalog-service=2

# Execute commands in containers
docker-compose exec [service-name] [command]
```

### Environment Variables

Each service can be configured using environment variables:

```bash
# Auth Service
JWT_SECRET=your-secret-key
MONGODB_URI=mongodb://mongodb:27017/auth

# Catalog Service
MONGODB_URI=mongodb://mongodb:27017/catalog

# Order Service
MONGODB_URI=mongodb://mongodb:27017/orders
```

## 🐛 Troubleshooting

### Common Issues

#### Docker Permission Issues (Linux)
```bash
# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Or run with sudo
sudo docker-compose up -d
```

#### SSL Certificate Issues
```bash
# Regenerate certificates
cd certs
rm -f *.pem
mkcert localhost 127.0.0.1 ::1
mv localhost+2.pem cert.pem
mv localhost+2-key.pem key.pem
```

#### Port Conflicts
```bash
# Check what's using the ports
netstat -tulpn | grep :3002
netstat -tulpn | grep :8001

# Stop conflicting services or change ports in docker-compose.yml
```

#### Container Build Issues
```bash
# Clean Docker cache
docker system prune -a

# Rebuild without cache
docker-compose build --no-cache
```

### Logs and Debugging

```bash
# View all logs
docker-compose logs

# View specific service logs
docker-compose logs frontend
docker-compose logs auth-service

# Follow logs in real-time
docker-compose logs -f

# View last 100 lines
docker-compose logs --tail=100
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **React.js** for the frontend framework
- **Node.js** and **Express** for the backend services
- **MongoDB** for the database
- **Docker** for containerization
- **mkcert** for SSL certificate generation
- **i18next** for internationalization

## 📞 Support

If you encounter any issues:

1. Check the [Troubleshooting](#-troubleshooting) section
2. Review the logs using `docker-compose logs`
3. Open an issue on GitHub with detailed error information

---

**Made with ❤️ for confectionery businesses worldwide** 🍰 