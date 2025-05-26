# 📦 Installation Scripts Overview

This document provides an overview of all installation scripts available for the Mimikurs e-commerce platform.

## 🎯 Available Scripts

### 🐧 Linux Installation

#### `install.sh` - Main Linux Installer
- **Supports**: Arch Linux, Debian/Ubuntu, RHEL/CentOS/Fedora
- **Features**:
  - Automatic distribution detection
  - Docker and Docker Compose installation
  - mkcert SSL certificate generation
  - Dependency management
  - Service health checks
  - Colorful output with progress indicators

**Usage:**
```bash
chmod +x install.sh
./install.sh
```

### 🪟 Windows Installation

#### `install.ps1` - PowerShell Installer
- **Supports**: Windows 10/11 with PowerShell 5.1+
- **Features**:
  - Chocolatey package manager installation
  - Docker Desktop installation
  - mkcert SSL certificate generation
  - Administrator privilege checking
  - Automatic restart handling
  - Comprehensive error handling

**Usage:**
```powershell
# Run as Administrator
.\install.ps1

# With options
.\install.ps1 -SkipDockerDesktop
.\install.ps1 -Force
```

#### `install.bat` - Batch File Wrapper
- **Supports**: Windows 10/11 with cmd.exe
- **Features**:
  - Calls PowerShell installer with proper execution policy
  - Administrator privilege checking
  - Simple command-line interface
  - Error handling and user feedback

**Usage:**
```cmd
# Right-click and "Run as administrator"
install.bat

# Or from elevated cmd
install.bat
```

### 🧪 Testing and Validation

#### `test-install.sh` - Installation Validator
- **Purpose**: Validates installation scripts and project structure
- **Features**:
  - File existence checks
  - Script syntax validation
  - Docker Compose configuration validation
  - Service definition verification
  - Documentation completeness check

**Usage:**
```bash
chmod +x test-install.sh
./test-install.sh
```

## 🔧 What Each Script Does

### Common Installation Steps

1. **System Detection**: Identifies operating system and version
2. **Dependency Installation**: Installs required packages (Docker, mkcert, etc.)
3. **SSL Certificate Generation**: Creates localhost SSL certificates
4. **Service Startup**: Builds and starts all microservices
5. **Health Checks**: Verifies all services are running properly
6. **User Guidance**: Provides access URLs and default credentials

### Platform-Specific Features

#### Linux (`install.sh`)
- **Package Managers**: pacman (Arch), apt (Debian/Ubuntu), dnf (RHEL/Fedora)
- **Service Management**: systemctl for Docker daemon
- **User Groups**: Automatic docker group management
- **Architecture Detection**: Supports x86_64, ARM64, ARM

#### Windows (`install.ps1`)
- **Package Manager**: Chocolatey for software installation
- **Docker Desktop**: Full Docker Desktop installation
- **Registry Management**: PATH environment variable updates
- **Restart Handling**: Automatic restart prompts for Docker Desktop

## 📋 Prerequisites by Platform

### Linux Requirements
- **OS**: Arch Linux, Debian/Ubuntu, RHEL/CentOS/Fedora
- **Privileges**: sudo access
- **Network**: Internet connection for package downloads
- **Disk Space**: ~2GB for Docker images

### Windows Requirements
- **OS**: Windows 10/11
- **Privileges**: Administrator access
- **PowerShell**: Version 5.1 or later
- **Network**: Internet connection for package downloads
- **Disk Space**: ~4GB for Docker Desktop and images

## 🚀 Quick Start Commands

### Linux
```bash
# One-line installation
curl -sSL https://raw.githubusercontent.com/your-repo/mimikurs/main/install.sh | bash

# Or clone and run
git clone https://github.com/your-repo/mimikurs.git
cd mimikurs
chmod +x install.sh
./install.sh
```

### Windows PowerShell
```powershell
# Clone and run
git clone https://github.com/your-repo/mimikurs.git
cd mimikurs
.\install.ps1
```

### Windows Command Prompt
```cmd
# Clone and run
git clone https://github.com/your-repo/mimikurs.git
cd mimikurs
install.bat
```

## 🔍 Script Options and Flags

### Linux (`install.sh`)
- No command-line options (fully automatic)
- Uses environment variables for customization

### Windows (`install.ps1`)
- `-SkipDockerDesktop`: Skip Docker Desktop installation
- `-Force`: Force installation even if components exist
- `-h`, `--help`, `/?`: Show help message

### Batch File (`install.bat`)
- Passes all arguments to PowerShell script
- Supports same options as `install.ps1`

## 🛠️ Customization

### Environment Variables
```bash
# Linux
export JWT_SECRET="your-custom-secret"
export MONGO_URI="mongodb://custom-host:27017"

# Windows
$env:JWT_SECRET = "your-custom-secret"
$env:MONGO_URI = "mongodb://custom-host:27017"
```

### Docker Compose Override
Create `docker-compose.override.yml` for custom configurations:
```yaml
version: '3.8'
services:
  frontend:
    ports:
      - "8080:3002"  # Custom port
```

## 🐛 Troubleshooting

### Common Issues

#### Permission Denied (Linux)
```bash
# Fix script permissions
chmod +x install.sh

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

#### Execution Policy (Windows)
```powershell
# Allow script execution
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Or run with bypass
powershell -ExecutionPolicy Bypass -File install.ps1
```

#### Docker Not Starting
```bash
# Linux
sudo systemctl start docker
sudo systemctl enable docker

# Windows
# Start Docker Desktop manually
```

### Log Files

Scripts create log files for debugging:
- Linux: `/tmp/mimikurs-install.log`
- Windows: `%TEMP%\mimikurs-install.log`

## 📞 Support

If installation fails:

1. **Check Prerequisites**: Ensure your system meets requirements
2. **Run Test Script**: Use `test-install.sh` to validate setup
3. **Check Logs**: Review installation logs for errors
4. **Manual Installation**: Follow manual steps in README.md
5. **Open Issue**: Report problems on GitHub with log files

## 🔄 Updates

To update installation scripts:

```bash
# Pull latest changes
git pull origin main

# Re-run installation
./install.sh  # Linux
.\install.ps1  # Windows
```

---

**All scripts are designed to be idempotent - safe to run multiple times!** 🔄 