#!/bin/bash

# Install mkcert locally trusted certificates setup script
# This script will install mkcert and set up the root CA for your browser

echo "🔐 Setting up mkcert for locally trusted certificates..."

# Check if mkcert is installed
if ! command -v mkcert &> /dev/null; then
    echo "📦 Installing mkcert..."
    
    # Detect OS and install mkcert
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        if command -v pacman &> /dev/null; then
            # Arch Linux
            sudo pacman -S mkcert
        elif command -v apt &> /dev/null; then
            # Ubuntu/Debian
            sudo apt update
            sudo apt install libnss3-tools
            curl -JLO "https://dl.filippo.io/mkcert/latest?for=linux/amd64"
            chmod +x mkcert-v*-linux-amd64
            sudo mv mkcert-v*-linux-amd64 /usr/local/bin/mkcert
        elif command -v yum &> /dev/null; then
            # CentOS/RHEL
            sudo yum install nss-tools
            curl -JLO "https://dl.filippo.io/mkcert/latest?for=linux/amd64"
            chmod +x mkcert-v*-linux-amd64
            sudo mv mkcert-v*-linux-amd64 /usr/local/bin/mkcert
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command -v brew &> /dev/null; then
            brew install mkcert
        else
            echo "❌ Please install Homebrew first: https://brew.sh/"
            exit 1
        fi
    else
        echo "❌ Unsupported OS. Please install mkcert manually: https://github.com/FiloSottile/mkcert"
        exit 1
    fi
else
    echo "✅ mkcert is already installed"
fi

# Install the local CA
echo "🔧 Installing mkcert root CA..."
mkcert -install

echo "✅ Setup complete!"
echo ""
echo "🌐 Your browser should now trust certificates for:"
echo "   • https://localhost:3002"
echo "   • https://127.0.0.1:3002"
echo ""
echo "🔄 Please restart your browser and try accessing https://localhost:3002"
echo ""
echo "📝 Note: The certificate is only trusted on this machine."
echo "   Other devices will still show security warnings." 