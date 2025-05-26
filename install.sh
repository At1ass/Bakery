#!/bin/bash

# Mimikurs E-commerce Platform - Linux Installation Script
# Supports: Arch Linux, Debian/Ubuntu, RHEL/CentOS/Fedora

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ASCII Art Banner
print_banner() {
    echo -e "${PURPLE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                    🍰 MIMIKURS INSTALLER 🍰                  ║"
    echo "║              Confectionery E-commerce Platform              ║"
    echo "║                     Linux Installation                      ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${CYAN}[STEP]${NC} $1"
}

# Detect Linux distribution
detect_distro() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        DISTRO=$ID
        VERSION=$VERSION_ID
    elif [ -f /etc/redhat-release ]; then
        DISTRO="rhel"
    elif [ -f /etc/debian_version ]; then
        DISTRO="debian"
    elif [ -f /etc/arch-release ]; then
        DISTRO="arch"
    else
        log_error "Cannot detect Linux distribution"
        exit 1
    fi
    
    log_info "Detected distribution: $DISTRO"
}

# Check if running as root
check_root() {
    if [ "$EUID" -eq 0 ]; then
        log_warning "Running as root. This script should be run as a regular user with sudo privileges."
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# Install Docker
install_docker() {
    log_step "Installing Docker..."
    
    case $DISTRO in
        "arch"|"manjaro")
            sudo pacman -Sy --noconfirm docker docker-compose
            ;;
        "ubuntu"|"debian"|"pop"|"linuxmint")
            # Remove old versions
            sudo apt-get remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true
            
            # Update package index
            sudo apt-get update
            
            # Install dependencies
            sudo apt-get install -y \
                ca-certificates \
                curl \
                gnupg \
                lsb-release
            
            # Add Docker's official GPG key
            sudo mkdir -p /etc/apt/keyrings
            curl -fsSL https://download.docker.com/linux/$DISTRO/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
            
            # Set up repository
            echo \
                "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/$DISTRO \
                $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
            
            # Install Docker Engine
            sudo apt-get update
            sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
            
            # Install docker-compose (standalone)
            sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
            sudo chmod +x /usr/local/bin/docker-compose
            ;;
        "fedora"|"centos"|"rhel"|"rocky"|"almalinux")
            # Remove old versions
            sudo dnf remove -y docker docker-client docker-client-latest docker-common docker-latest docker-latest-logrotate docker-logrotate docker-selinux docker-engine-selinux docker-engine 2>/dev/null || true
            
            # Install dependencies
            sudo dnf install -y dnf-plugins-core
            
            # Add Docker repository
            sudo dnf config-manager --add-repo https://download.docker.com/linux/fedora/docker-ce.repo
            
            # Install Docker
            sudo dnf install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
            
            # Install docker-compose (standalone)
            sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
            sudo chmod +x /usr/local/bin/docker-compose
            ;;
        *)
            log_error "Unsupported distribution for automatic Docker installation: $DISTRO"
            log_info "Please install Docker manually and run this script again."
            exit 1
            ;;
    esac
    
    # Start and enable Docker service
    sudo systemctl start docker
    sudo systemctl enable docker
    
    # Add current user to docker group
    sudo usermod -aG docker $USER
    
    log_success "Docker installed successfully"
}

# Install mkcert for SSL certificates
install_mkcert() {
    log_step "Installing mkcert for SSL certificates..."
    
    case $DISTRO in
        "arch"|"manjaro")
            # Check if mkcert is available in official repos
            if pacman -Ss mkcert | grep -q "community/mkcert"; then
                sudo pacman -S --noconfirm mkcert
            else
                # Install from AUR or binary
                install_mkcert_binary
            fi
            ;;
        "ubuntu"|"debian"|"pop"|"linuxmint")
            # Install dependencies
            sudo apt-get update
            sudo apt-get install -y wget curl
            
            # Install mkcert binary
            install_mkcert_binary
            ;;
        "fedora"|"centos"|"rhel"|"rocky"|"almalinux")
            # Install dependencies
            sudo dnf install -y wget curl
            
            # Install mkcert binary
            install_mkcert_binary
            ;;
        *)
            install_mkcert_binary
            ;;
    esac
    
    log_success "mkcert installed successfully"
}

# Install mkcert binary
install_mkcert_binary() {
    log_info "Installing mkcert from binary..."
    
    # Detect architecture
    ARCH=$(uname -m)
    case $ARCH in
        x86_64)
            MKCERT_ARCH="amd64"
            ;;
        aarch64|arm64)
            MKCERT_ARCH="arm64"
            ;;
        armv7l)
            MKCERT_ARCH="arm"
            ;;
        *)
            log_error "Unsupported architecture: $ARCH"
            exit 1
            ;;
    esac
    
    # Download and install mkcert
    MKCERT_VERSION=$(curl -s https://api.github.com/repos/FiloSottile/mkcert/releases/latest | grep '"tag_name":' | sed -E 's/.*"([^"]+)".*/\1/')
    wget -O mkcert "https://github.com/FiloSottile/mkcert/releases/download/${MKCERT_VERSION}/mkcert-${MKCERT_VERSION}-linux-${MKCERT_ARCH}"
    chmod +x mkcert
    sudo mv mkcert /usr/local/bin/
}

# Install additional dependencies
install_dependencies() {
    log_step "Installing additional dependencies..."
    
    case $DISTRO in
        "arch"|"manjaro")
            sudo pacman -S --noconfirm git curl wget unzip
            ;;
        "ubuntu"|"debian"|"pop"|"linuxmint")
            sudo apt-get update
            sudo apt-get install -y git curl wget unzip build-essential
            ;;
        "fedora"|"centos"|"rhel"|"rocky"|"almalinux")
            sudo dnf install -y git curl wget unzip gcc gcc-c++ make
            ;;
    esac
    
    log_success "Dependencies installed successfully"
}

# Setup SSL certificates
setup_ssl() {
    log_step "Setting up SSL certificates..."
    
    # Create certs directory
    mkdir -p certs
    cd certs
    
    # Install CA
    mkcert -install
    
    # Generate certificates for localhost
    mkcert localhost 127.0.0.1 ::1
    
    # Rename files to match docker-compose expectations
    mv localhost+2.pem cert.pem
    mv localhost+2-key.pem key.pem
    
    cd ..
    
    log_success "SSL certificates generated successfully"
}

# Check if Docker is running
check_docker() {
    log_step "Checking Docker installation..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed or not in PATH"
        return 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed or not in PATH"
        return 1
    fi
    
    # Check if Docker daemon is running
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running"
        log_info "Starting Docker service..."
        sudo systemctl start docker
        sleep 3
        
        if ! docker info &> /dev/null; then
            log_error "Failed to start Docker daemon"
            return 1
        fi
    fi
    
    log_success "Docker is running properly"
    return 0
}

# Build and run containers
run_application() {
    log_step "Building and starting the application..."
    
    # Stop any existing containers
    docker-compose down 2>/dev/null || true
    
    # Build and start containers
    docker-compose up --build -d
    
    # Wait for services to start
    log_info "Waiting for services to start..."
    sleep 10
    
    # Check if containers are running
    if docker-compose ps | grep -q "Up"; then
        log_success "Application started successfully!"
        echo
        echo -e "${GREEN}🎉 Installation completed successfully! 🎉${NC}"
        echo
        echo -e "${CYAN}Access your application at:${NC}"
        echo -e "  🌐 Frontend: ${YELLOW}https://localhost:3002${NC}"
        echo -e "  🔧 API: ${YELLOW}http://localhost:8001${NC} (Auth)"
        echo -e "  📦 API: ${YELLOW}http://localhost:8002${NC} (Catalog)"
        echo -e "  🛒 API: ${YELLOW}http://localhost:8003${NC} (Orders)"
        echo
        echo -e "${BLUE}Default credentials:${NC}"
        echo -e "  📧 Email: ${YELLOW}admin@mimikurs.com${NC}"
        echo -e "  🔑 Password: ${YELLOW}admin123${NC}"
        echo
        echo -e "${PURPLE}To stop the application: ${YELLOW}docker-compose down${NC}"
        echo -e "${PURPLE}To view logs: ${YELLOW}docker-compose logs -f${NC}"
        echo -e "${PURPLE}To restart: ${YELLOW}docker-compose restart${NC}"
        echo
    else
        log_error "Some containers failed to start"
        echo "Container status:"
        docker-compose ps
        echo
        echo "Logs:"
        docker-compose logs
        exit 1
    fi
}

# Handle user groups (Docker)
handle_groups() {
    if groups $USER | grep -q docker; then
        log_info "User is already in docker group"
    else
        log_warning "User needs to be added to docker group"
        log_info "You may need to log out and log back in, or run: newgrp docker"
        
        # Try to use newgrp if available
        if command -v newgrp &> /dev/null; then
            log_info "Attempting to refresh group membership..."
            exec newgrp docker "$0" "$@"
        fi
    fi
}

# Cleanup function
cleanup() {
    log_info "Cleaning up temporary files..."
    # Add any cleanup tasks here
}

# Main installation function
main() {
    print_banner
    
    log_info "Starting Mimikurs installation..."
    echo
    
    # Trap cleanup on exit
    trap cleanup EXIT
    
    # Check if running as root
    check_root
    
    # Detect distribution
    detect_distro
    
    # Install dependencies
    install_dependencies
    
    # Install Docker if not present
    if ! command -v docker &> /dev/null; then
        install_docker
        handle_groups
    else
        log_info "Docker is already installed"
        check_docker || exit 1
    fi
    
    # Install mkcert if not present
    if ! command -v mkcert &> /dev/null; then
        install_mkcert
    else
        log_info "mkcert is already installed"
    fi
    
    # Setup SSL certificates
    if [ ! -f "certs/cert.pem" ] || [ ! -f "certs/key.pem" ]; then
        setup_ssl
    else
        log_info "SSL certificates already exist"
    fi
    
    # Final Docker check
    check_docker || exit 1
    
    # Run the application
    run_application
}

# Check if docker-compose.yml exists
if [ ! -f "docker-compose.yml" ]; then
    log_error "docker-compose.yml not found in current directory"
    log_info "Please run this script from the project root directory"
    exit 1
fi

# Run main function
main "$@" 