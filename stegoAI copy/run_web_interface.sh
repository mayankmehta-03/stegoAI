#!/bin/bash

# ============================================
# StegoAI Web Interface - Quick Start Script
# ============================================

echo ""
echo "╔════════════════════════════════════════════╗"
echo "║     StegoAI - Web Interface Setup           ║"
echo "║   Advanced Steganography Platform           ║"
echo "╚════════════════════════════════════════════╝"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "✗ Python 3 not found!"
    echo "Please install Python 3.7 or higher"
    exit 1
fi

echo "✓ Python found: $(python3 --version)"
echo ""

# Verify virtual environment
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    echo "✓ Virtual environment created"
    echo ""
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate
if [ $? -ne 0 ]; then
    echo "✗ Failed to activate virtual environment"
    exit 1
fi
echo "✓ Virtual environment activated"
echo ""

# Install requirements
echo "Installing dependencies from requirements_web.txt..."
pip install -q -r requirements_web.txt
if [ $? -ne 0 ]; then
    echo "✗ Failed to install dependencies"
    echo "Please run: pip install -r requirements_web.txt"
    exit 1
fi
echo "✓ Dependencies installed successfully"
echo ""

# Verify model files
echo "Checking for model files..."
if [ ! -f "models/hide.h5" ]; then
    echo "✗ Missing: models/hide.h5"
    echo "✗ Please train the model first or copy it to the models folder"
    exit 1
fi
if [ ! -f "models/reveal.h5" ]; then
    echo "✗ Missing: models/reveal.h5"
    echo "✗ Please train the model first or copy it to the models folder"
    exit 1
fi
echo "✓ Model files found"
echo ""

# Create necessary directories
mkdir -p uploads
mkdir -p output
echo "✓ Directories ready"
echo ""

# Display startup message
echo "╔════════════════════════════════════════════╗"
echo "║   Starting StegoAI Web Server...            ║"
echo "║                                            ║"
echo "║   Open your browser and go to:             ║"
echo "║   http://localhost:5000                    ║"
echo "║                                            ║"
echo "║   Press Ctrl+C to stop the server          ║"
echo "╚════════════════════════════════════════════╝"
echo ""

# Start Flask app
python3 app.py
