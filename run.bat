@echo off
REM Watch Data Scraper & Wix Porter - Quick Start Script
REM This script sets up and runs the application

echo.
echo ========================================
echo Watch Data Scraper and Wix Porter
echo Quick Start Installation
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

echo [1/5] Python found! Creating virtual environment...
python -m venv venv

echo [2/5] Activating virtual environment...
call venv\Scripts\activate.bat

echo [3/5] Upgrading pip...
python -m pip install --upgrade pip

echo [4/5] Installing dependencies...
pip install -r requirements.txt

echo [5/5] Setup complete!
echo.
echo ========================================
echo Starting Flask Application...
echo ========================================
echo.
echo Opening browser to: http://localhost:5000
echo Press Ctrl+C to stop the server
echo.

timeout /t 2 >nul
python app.py
