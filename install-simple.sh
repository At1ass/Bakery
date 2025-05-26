#!/bin/bash

# Mimikurs Installation Script (HTTP-only version)
# This script installs and runs the Mimikurs confectionery management system

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_step() {
    echo -e "${PURPLE}🔄 $1${NC}"
}

# Print banner
print_banner() {
    echo -e "${CYAN}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                    🧁 MIMIKURS INSTALLER 🧁                  ║"
    echo "║              Confectionery Management System                 ║"
    echo "║                     HTTP-Only Version                       ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_error "This script should not be run as root"
        log_info "Please run as a regular user with sudo privileges"
        exit 1
    fi
}

# Detect Linux distribution
detect_distro() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        DISTRO=$ID
        VERSION=$VERSION_ID
    else
        log_error "Cannot detect Linux distribution"
        exit 1
    fi
    
    log_info "Detected distribution: $DISTRO $VERSION"
}

# Install Docker
install_docker() {
    log_step "Installing Docker..."
    
    case $DISTRO in
        "arch"|"manjaro")
            sudo pacman -S --noconfirm docker docker-compose
            ;;
        "ubuntu"|"debian"|"pop"|"linuxmint")
            # Update package index
            sudo apt-get update
            
            # Install prerequisites
            sudo apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release
            
            # Add Docker's official GPG key
            curl -fsSL https://download.docker.com/linux/$DISTRO/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
            
            # Add Docker repository
            echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/$DISTRO $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
            
            # Install Docker
            sudo apt-get update
            sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
            
            # Install docker-compose
            sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
            sudo chmod +x /usr/local/bin/docker-compose
            ;;
        "fedora"|"centos"|"rhel"|"rocky"|"almalinux")
            # Install Docker
            sudo dnf install -y docker docker-compose
            ;;
        *)
            log_error "Unsupported distribution: $DISTRO"
            exit 1
            ;;
    esac
    
    # Add user to docker group
    sudo usermod -aG docker $USER
    
    # Enable and start Docker service
    sudo systemctl enable docker
    sudo systemctl start docker
    
    log_success "Docker installed successfully"
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
    sleep 15
    
    # Check if containers are running
    if docker-compose ps | grep -q "Up"; then
        log_success "Application started successfully!"
        echo
        echo -e "${GREEN}🎉 Installation completed successfully! 🎉${NC}"
        echo
        echo -e "${CYAN}Access your application at:${NC}"
        echo -e "  🌐 Frontend: ${YELLOW}http://localhost:3001${NC}"
        echo -e "  🔧 API: ${YELLOW}http://localhost:8001${NC} (Auth)"
        echo -e "  📦 API: ${YELLOW}http://localhost:8002${NC} (Catalog)"
        echo -e "  🛒 API: ${YELLOW}http://localhost:8003${NC} (Orders)"
        echo
        echo -e "${BLUE}Default test credentials:${NC}"
        echo -e "  📧 Email: ${YELLOW}test@example.com${NC}"
        echo -e "  🔑 Password: ${YELLOW}TestPassword123!${NC}"
        echo
        echo -e "${PURPLE}Useful commands:${NC}"
        echo -e "  Stop: ${YELLOW}docker-compose down${NC}"
        echo -e "  Logs: ${YELLOW}docker-compose logs -f${NC}"
        echo -e "  Restart: ${YELLOW}docker-compose restart${NC}"
        echo -e "  Status: ${YELLOW}docker-compose ps${NC}"
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
    
    log_info "Starting Mimikurs installation (HTTP-only)..."
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