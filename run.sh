#!/bin/bash
# Watch Data Scraper & Wix Porter - Quick Start Script for macOS/Linux

echo ""
echo "========================================"
echo "Watch Data Scraper & Wix Porter"
echo "Quick Start Installation"
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.8+ from https://www.python.org"
    exit 1
fi

echo "[1/5] Python found! Creating virtual environment..."
python3 -m venv venv

echo "[2/5] Activating virtual environment..."
source venv/bin/activate

echo "[3/5] Upgrading pip..."
python -m pip install --upgrade pip

echo "[4/5] Installing dependencies..."
pip install -r requirements.txt

echo "[5/5] Setup complete!"
echo ""
echo "========================================"
echo "Starting Flask Application..."
echo "========================================"
echo ""
echo "Opening browser to: http://localhost:5000"
echo "Press Ctrl+C to stop the server"
echo ""

sleep 2
python app.py
