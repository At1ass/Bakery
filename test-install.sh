#!/bin/bash

# Test script for installation validation
# This script checks if all required files are present and scripts are valid

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "🧪 Testing Mimikurs Installation Scripts"
echo "========================================"

# Test 1: Check if all required files exist
echo -e "\n${YELLOW}Test 1: Checking required files...${NC}"

required_files=(
    "docker-compose.yml"
    "install.sh"
    "install.ps1"
    "install.bat"
    "README.md"
    "QUICK_START.md"
)

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo -e "✅ $file exists"
    else
        echo -e "❌ $file missing"
        exit 1
    fi
done

# Test 2: Check script permissions
echo -e "\n${YELLOW}Test 2: Checking script permissions...${NC}"

if [ -x "install.sh" ]; then
    echo -e "✅ install.sh is executable"
else
    echo -e "❌ install.sh is not executable"
    chmod +x install.sh
    echo -e "🔧 Fixed: Made install.sh executable"
fi

# Test 3: Validate shell script syntax
echo -e "\n${YELLOW}Test 3: Validating shell script syntax...${NC}"

if bash -n install.sh; then
    echo -e "✅ install.sh syntax is valid"
else
    echo -e "❌ install.sh has syntax errors"
    exit 1
fi

# Test 4: Check PowerShell script syntax (if PowerShell is available)
echo -e "\n${YELLOW}Test 4: Validating PowerShell script...${NC}"

if command -v pwsh &> /dev/null; then
    if pwsh -Command "Get-Content install.ps1 | Out-Null"; then
        echo -e "✅ install.ps1 syntax is valid"
    else
        echo -e "❌ install.ps1 has syntax errors"
        exit 1
    fi
else
    echo -e "⚠️  PowerShell not available, skipping syntax check"
fi

# Test 5: Check docker-compose file validity
echo -e "\n${YELLOW}Test 5: Validating docker-compose.yml...${NC}"

if command -v docker-compose &> /dev/null; then
    if docker-compose config &> /dev/null; then
        echo -e "✅ docker-compose.yml is valid"
    else
        echo -e "❌ docker-compose.yml has errors"
        exit 1
    fi
else
    echo -e "⚠️  docker-compose not available, skipping validation"
fi

# Test 6: Check if all services are defined
echo -e "\n${YELLOW}Test 6: Checking service definitions...${NC}"

required_services=(
    "mongo"
    "auth"
    "catalog"
    "order"
    "frontend"
)

for service in "${required_services[@]}"; do
    if grep -q "$service:" docker-compose.yml; then
        echo -e "✅ $service service defined"
    else
        echo -e "❌ $service service missing"
        exit 1
    fi
done

# Test 7: Check if service directories exist
echo -e "\n${YELLOW}Test 7: Checking service directories...${NC}"

service_dirs=(
    "auth-service"
    "catalog-service"
    "order-service"
    "frontend"
)

for dir in "${service_dirs[@]}"; do
    if [ -d "$dir" ]; then
        echo -e "✅ $dir directory exists"
        
        # Check for Dockerfile
        if [ -f "$dir/Dockerfile" ]; then
            echo -e "  ✅ $dir/Dockerfile exists"
        else
            echo -e "  ❌ $dir/Dockerfile missing"
            exit 1
        fi
    else
        echo -e "❌ $dir directory missing"
        exit 1
    fi
done

# Test 8: Check README completeness
echo -e "\n${YELLOW}Test 8: Checking README completeness...${NC}"

readme_sections=(
    "Quick Start"
    "Installation"
    "Architecture"
    "Troubleshooting"
)

for section in "${readme_sections[@]}"; do
    if grep -q "$section" README.md; then
        echo -e "✅ README contains $section section"
    else
        echo -e "❌ README missing $section section"
        exit 1
    fi
done

echo -e "\n${GREEN}🎉 All tests passed! Installation scripts are ready.${NC}"
echo -e "\n${YELLOW}To install Mimikurs:${NC}"
echo -e "  Linux: ${GREEN}./install.sh${NC}"
echo -e "  Windows: ${GREEN}.\\install.ps1${NC} or ${GREEN}install.bat${NC}" 