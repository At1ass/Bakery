# Mimikurs E-commerce Platform - Windows Installation Script
# Requires: Windows 10/11, PowerShell 5.1+

param(
    [switch]$SkipDockerDesktop,
    [switch]$Force
)

# Set execution policy for this session
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process -Force

# Colors for output
$Colors = @{
    Red = "Red"
    Green = "Green"
    Yellow = "Yellow"
    Blue = "Blue"
    Magenta = "Magenta"
    Cyan = "Cyan"
    White = "White"
}

# ASCII Art Banner
function Show-Banner {
    Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Magenta
    Write-Host "║                    🍰 MIMIKURS INSTALLER 🍰                  ║" -ForegroundColor Magenta
    Write-Host "║              Confectionery E-commerce Platform              ║" -ForegroundColor Magenta
    Write-Host "║                    Windows Installation                     ║" -ForegroundColor Magenta
    Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Magenta
    Write-Host ""
}

# Logging functions
function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

function Write-Step {
    param([string]$Message)
    Write-Host "[STEP] $Message" -ForegroundColor Cyan
}

# Check if running as administrator
function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# Check Windows version
function Test-WindowsVersion {
    $version = [System.Environment]::OSVersion.Version
    if ($version.Major -lt 10) {
        Write-Error "Windows 10 or later is required"
        return $false
    }
    Write-Info "Windows version: $($version.Major).$($version.Minor)"
    return $true
}

# Install Chocolatey package manager
function Install-Chocolatey {
    Write-Step "Installing Chocolatey package manager..."
    
    if (Get-Command choco -ErrorAction SilentlyContinue) {
        Write-Info "Chocolatey is already installed"
        return
    }
    
    try {
        Set-ExecutionPolicy Bypass -Scope Process -Force
        [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
        Invoke-Expression ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
        
        # Refresh environment variables
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
        
        Write-Success "Chocolatey installed successfully"
    }
    catch {
        Write-Error "Failed to install Chocolatey: $($_.Exception.Message)"
        throw
    }
}

# Install Docker Desktop
function Install-DockerDesktop {
    Write-Step "Installing Docker Desktop..."
    
    if (Get-Command docker -ErrorAction SilentlyContinue) {
        Write-Info "Docker is already installed"
        return
    }
    
    if ($SkipDockerDesktop) {
        Write-Warning "Skipping Docker Desktop installation as requested"
        Write-Info "Please install Docker Desktop manually from https://www.docker.com/products/docker-desktop"
        return
    }
    
    try {
        # Install Docker Desktop via Chocolatey
        choco install docker-desktop -y
        
        Write-Success "Docker Desktop installed successfully"
        Write-Warning "Please restart your computer and start Docker Desktop before continuing"
        Write-Info "After restart, run this script again to continue the installation"
        
        $restart = Read-Host "Do you want to restart now? (y/N)"
        if ($restart -eq 'y' -or $restart -eq 'Y') {
            Restart-Computer -Force
        }
        exit 0
    }
    catch {
        Write-Error "Failed to install Docker Desktop: $($_.Exception.Message)"
        Write-Info "Please install Docker Desktop manually from https://www.docker.com/products/docker-desktop"
        throw
    }
}

# Install mkcert
function Install-Mkcert {
    Write-Step "Installing mkcert for SSL certificates..."
    
    if (Get-Command mkcert -ErrorAction SilentlyContinue) {
        Write-Info "mkcert is already installed"
        return
    }
    
    try {
        choco install mkcert -y
        
        # Refresh environment variables
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
        
        Write-Success "mkcert installed successfully"
    }
    catch {
        Write-Error "Failed to install mkcert: $($_.Exception.Message)"
        Write-Info "Trying to install mkcert manually..."
        Install-MkcertManual
    }
}

# Install mkcert manually
function Install-MkcertManual {
    Write-Info "Installing mkcert manually..."
    
    try {
        # Create tools directory
        $toolsDir = "$env:USERPROFILE\tools"
        if (!(Test-Path $toolsDir)) {
            New-Item -ItemType Directory -Path $toolsDir -Force | Out-Null
        }
        
        # Download mkcert
        $mkcertUrl = "https://github.com/FiloSottile/mkcert/releases/latest/download/mkcert-v1.4.4-windows-amd64.exe"
        $mkcertPath = "$toolsDir\mkcert.exe"
        
        Write-Info "Downloading mkcert..."
        Invoke-WebRequest -Uri $mkcertUrl -OutFile $mkcertPath
        
        # Add to PATH
        $currentPath = [Environment]::GetEnvironmentVariable("Path", "User")
        if ($currentPath -notlike "*$toolsDir*") {
            [Environment]::SetEnvironmentVariable("Path", "$currentPath;$toolsDir", "User")
            $env:Path += ";$toolsDir"
        }
        
        Write-Success "mkcert installed manually"
    }
    catch {
        Write-Error "Failed to install mkcert manually: $($_.Exception.Message)"
        throw
    }
}

# Install additional dependencies
function Install-Dependencies {
    Write-Step "Installing additional dependencies..."
    
    try {
        # Install Git if not present
        if (!(Get-Command git -ErrorAction SilentlyContinue)) {
            Write-Info "Installing Git..."
            choco install git -y
        }
        
        # Install curl if not present
        if (!(Get-Command curl -ErrorAction SilentlyContinue)) {
            Write-Info "Installing curl..."
            choco install curl -y
        }
        
        # Refresh environment variables
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
        
        Write-Success "Dependencies installed successfully"
    }
    catch {
        Write-Error "Failed to install dependencies: $($_.Exception.Message)"
        throw
    }
}

# Setup SSL certificates
function Set-SSLCertificates {
    Write-Step "Setting up SSL certificates..."
    
    try {
        # Create certs directory
        if (!(Test-Path "certs")) {
            New-Item -ItemType Directory -Path "certs" -Force | Out-Null
        }
        
        Set-Location "certs"
        
        # Install CA
        Write-Info "Installing local CA..."
        & mkcert -install
        
        # Generate certificates for localhost
        Write-Info "Generating SSL certificates..."
        & mkcert localhost 127.0.0.1 ::1
        
        # Rename files to match docker-compose expectations
        if (Test-Path "localhost+2.pem") {
            Rename-Item "localhost+2.pem" "cert.pem"
        }
        if (Test-Path "localhost+2-key.pem") {
            Rename-Item "localhost+2-key.pem" "key.pem"
        }
        
        Set-Location ".."
        
        Write-Success "SSL certificates generated successfully"
    }
    catch {
        Write-Error "Failed to setup SSL certificates: $($_.Exception.Message)"
        throw
    }
}

# Check Docker installation and status
function Test-Docker {
    Write-Step "Checking Docker installation..."
    
    if (!(Get-Command docker -ErrorAction SilentlyContinue)) {
        Write-Error "Docker is not installed or not in PATH"
        return $false
    }
    
    if (!(Get-Command docker-compose -ErrorAction SilentlyContinue)) {
        Write-Error "Docker Compose is not installed or not in PATH"
        return $false
    }
    
    # Check if Docker daemon is running
    try {
        $dockerInfo = docker info 2>$null
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Docker daemon is not running"
            Write-Info "Please start Docker Desktop and try again"
            return $false
        }
    }
    catch {
        Write-Error "Docker daemon is not running"
        Write-Info "Please start Docker Desktop and try again"
        return $false
    }
    
    Write-Success "Docker is running properly"
    return $true
}

# Build and run the application
function Start-Application {
    Write-Step "Building and starting the application..."
    
    try {
        # Stop any existing containers
        Write-Info "Stopping existing containers..."
        docker-compose down 2>$null
        
        # Build and start containers
        Write-Info "Building and starting containers..."
        docker-compose up --build -d
        
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to start containers"
        }
        
        # Wait for services to start
        Write-Info "Waiting for services to start..."
        Start-Sleep -Seconds 10
        
        # Check if containers are running
        $runningContainers = docker-compose ps --filter "status=running" -q
        if ($runningContainers) {
            Write-Success "Application started successfully!"
            Write-Host ""
            Write-Host "🎉 Installation completed successfully! 🎉" -ForegroundColor Green
            Write-Host ""
            Write-Host "Access your application at:" -ForegroundColor Cyan
            Write-Host "  🌐 Frontend: " -NoNewline -ForegroundColor Cyan
            Write-Host "https://localhost:3002" -ForegroundColor Yellow
            Write-Host "  🔧 API: " -NoNewline -ForegroundColor Cyan
            Write-Host "http://localhost:8001" -NoNewline -ForegroundColor Yellow
            Write-Host " (Auth)" -ForegroundColor Cyan
            Write-Host "  📦 API: " -NoNewline -ForegroundColor Cyan
            Write-Host "http://localhost:8002" -NoNewline -ForegroundColor Yellow
            Write-Host " (Catalog)" -ForegroundColor Cyan
            Write-Host "  🛒 API: " -NoNewline -ForegroundColor Cyan
            Write-Host "http://localhost:8003" -NoNewline -ForegroundColor Yellow
            Write-Host " (Orders)" -ForegroundColor Cyan
            Write-Host ""
            Write-Host "Default credentials:" -ForegroundColor Blue
            Write-Host "  📧 Email: " -NoNewline -ForegroundColor Blue
            Write-Host "admin@mimikurs.com" -ForegroundColor Yellow
            Write-Host "  🔑 Password: " -NoNewline -ForegroundColor Blue
            Write-Host "admin123" -ForegroundColor Yellow
            Write-Host ""
            Write-Host "To stop the application: " -NoNewline -ForegroundColor Magenta
            Write-Host "docker-compose down" -ForegroundColor Yellow
            Write-Host "To view logs: " -NoNewline -ForegroundColor Magenta
            Write-Host "docker-compose logs -f" -ForegroundColor Yellow
            Write-Host "To restart: " -NoNewline -ForegroundColor Magenta
            Write-Host "docker-compose restart" -ForegroundColor Yellow
            Write-Host ""
        }
        else {
            Write-Error "Some containers failed to start"
            Write-Host "Container status:"
            docker-compose ps
            Write-Host ""
            Write-Host "Logs:"
            docker-compose logs
            throw "Application failed to start properly"
        }
    }
    catch {
        Write-Error "Failed to start application: $($_.Exception.Message)"
        throw
    }
}

# Main installation function
function Start-Installation {
    Show-Banner
    
    Write-Info "Starting Mimikurs installation for Windows..."
    Write-Host ""
    
    try {
        # Check if running as administrator
        if (!(Test-Administrator)) {
            Write-Error "This script must be run as Administrator"
            Write-Info "Please right-click on PowerShell and select 'Run as Administrator'"
            exit 1
        }
        
        # Check Windows version
        if (!(Test-WindowsVersion)) {
            exit 1
        }
        
        # Install Chocolatey
        Install-Chocolatey
        
        # Install dependencies
        Install-Dependencies
        
        # Install Docker Desktop if not present
        if (!(Get-Command docker -ErrorAction SilentlyContinue)) {
            Install-DockerDesktop
        }
        else {
            Write-Info "Docker is already installed"
        }
        
        # Check Docker status
        if (!(Test-Docker)) {
            Write-Error "Docker is not running properly"
            Write-Info "Please ensure Docker Desktop is started and try again"
            exit 1
        }
        
        # Install mkcert if not present
        if (!(Get-Command mkcert -ErrorAction SilentlyContinue)) {
            Install-Mkcert
        }
        else {
            Write-Info "mkcert is already installed"
        }
        
        # Setup SSL certificates
        if (!(Test-Path "certs\cert.pem") -or !(Test-Path "certs\key.pem")) {
            Set-SSLCertificates
        }
        else {
            Write-Info "SSL certificates already exist"
        }
        
        # Final Docker check
        if (!(Test-Docker)) {
            exit 1
        }
        
        # Start the application
        Start-Application
    }
    catch {
        Write-Error "Installation failed: $($_.Exception.Message)"
        Write-Info "Please check the error messages above and try again"
        exit 1
    }
}

# Check if docker-compose.yml exists
if (!(Test-Path "docker-compose.yml")) {
    Write-Error "docker-compose.yml not found in current directory"
    Write-Info "Please run this script from the project root directory"
    exit 1
}

# Show help if requested
if ($args -contains "-h" -or $args -contains "--help" -or $args -contains "/?") {
    Write-Host "Mimikurs Windows Installer" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Usage: .\install.ps1 [options]" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Options:" -ForegroundColor Green
    Write-Host "  -SkipDockerDesktop    Skip Docker Desktop installation" -ForegroundColor White
    Write-Host "  -Force                Force installation even if components exist" -ForegroundColor White
    Write-Host "  -h, --help, /?        Show this help message" -ForegroundColor White
    Write-Host ""
    Write-Host "Requirements:" -ForegroundColor Green
    Write-Host "  - Windows 10/11" -ForegroundColor White
    Write-Host "  - PowerShell 5.1 or later" -ForegroundColor White
    Write-Host "  - Administrator privileges" -ForegroundColor White
    Write-Host "  - Internet connection" -ForegroundColor White
    Write-Host ""
    exit 0
}

# Run the installation
Start-Installation 