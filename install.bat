@echo off
REM Mimikurs E-commerce Platform - Windows Batch Installer
REM This script calls the PowerShell installer with proper execution policy

setlocal EnableDelayedExpansion

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] This script must be run as Administrator
    echo Please right-click on this file and select "Run as administrator"
    pause
    exit /b 1
)

REM ASCII Banner
echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                    🍰 MIMIKURS INSTALLER 🍰                  ║
echo ║              Confectionery E-commerce Platform              ║
echo ║                    Windows Installation                     ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

REM Check if PowerShell is available
powershell -Command "exit 0" >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] PowerShell is not available or not working properly
    echo Please ensure PowerShell is installed and try again
    pause
    exit /b 1
)

REM Check if docker-compose.yml exists
if not exist "docker-compose.yml" (
    echo [ERROR] docker-compose.yml not found in current directory
    echo Please run this script from the project root directory
    pause
    exit /b 1
)

REM Show help if requested
if "%1"=="-h" goto :help
if "%1"=="--help" goto :help
if "%1"=="/?" goto :help
if "%1"=="help" goto :help

REM Run PowerShell installer
echo [INFO] Starting PowerShell installer...
echo.

powershell -ExecutionPolicy Bypass -File "install.ps1" %*

if %errorLevel% neq 0 (
    echo.
    echo [ERROR] Installation failed
    echo Please check the error messages above and try again
    pause
    exit /b 1
)

echo.
echo [SUCCESS] Installation completed successfully!
pause
exit /b 0

:help
echo Mimikurs Windows Installer
echo.
echo Usage: install.bat [options]
echo.
echo Options:
echo   -SkipDockerDesktop    Skip Docker Desktop installation
echo   -Force                Force installation even if components exist
echo   -h, --help, /?        Show this help message
echo.
echo Requirements:
echo   - Windows 10/11
echo   - PowerShell 5.1 or later
echo   - Administrator privileges
echo   - Internet connection
echo.
pause
exit /b 0 