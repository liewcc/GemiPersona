@echo off
title GemiPersona Environment Installer - v1.5.0
cd /d %~dp0

echo ==========================================
echo GemiPersona Environment Installer
echo ==========================================

:: 1. Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found! 
    echo Please install Python 3.10+ and check "Add Python to PATH".
    echo Download from: https://www.python.org/
    pause
    exit /b
)

:: 2. Create Virtual Environment
if not exist .venv (
    echo [1/4] Creating virtual environment...
    python -m venv .venv
) else (
    echo [1/4] Virtual environment already exists.
)

:: 3. Upgrade Pip
echo [2/4] Upgrading pip... 
.venv\Scripts\python.exe -m pip install --upgrade pip

:: 4. Install Dependencies
echo [3/4] Installing dependencies... 
.venv\Scripts\pip install -r requirements.txt 

:: 5. Install Playwright Browser Core
echo [4/4] Installing Chromium browser engine... 
.venv\Scripts\playwright install chromium 

echo ==========================================
echo Installation Complete! 
echo You can now use run.bat to start the app.
echo ==========================================
pause