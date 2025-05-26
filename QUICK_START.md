# 🚀 Quick Start Guide

Get Mimikurs running in 5 minutes!

## 🐧 Linux Users

```bash
# 1. Make script executable
chmod +x install.sh

# 2. Run installer
./install.sh

# 3. Access your app at https://localhost:3002
```

## 🪟 Windows Users

### Option A: PowerShell (Recommended)
```powershell
# 1. Right-click PowerShell → "Run as Administrator"
# 2. Navigate to project folder
# 3. Run installer
.\install.ps1
```

### Option B: Batch File
```cmd
# 1. Right-click install.bat → "Run as administrator"
# 2. Follow the prompts
```

## 🎯 What You Get

After installation:

- ✅ **Frontend**: https://localhost:3002
- ✅ **APIs**: http://localhost:8001-8003
- ✅ **SSL Certificates**: Auto-generated
- ✅ **Sample Data**: Pre-loaded products

## 🔑 Default Login

- **Email**: `admin@mimikurs.com`
- **Password**: `admin123`

## 🌍 Language Support

- 🇺🇸 English (default)
- 🇷🇺 Russian (Русский)

Switch languages using the flag icons in the header!

## 🛑 Troubleshooting

### Docker Issues
```bash
# Check if Docker is running
docker --version
docker-compose --version

# Start Docker (Linux)
sudo systemctl start docker
```

### SSL Certificate Issues
```bash
# Regenerate certificates
cd certs
rm -f *.pem
mkcert localhost 127.0.0.1 ::1
mv localhost+2.pem cert.pem
mv localhost+2-key.pem key.pem
```

### Port Conflicts
```bash
# Check what's using port 3002
netstat -tulpn | grep :3002

# Stop the application
docker-compose down
```

## 📞 Need Help?

1. Check the full [README.md](README.md)
2. View logs: `docker-compose logs -f`
3. Open an issue on GitHub

---

**Happy selling! 🍰** 