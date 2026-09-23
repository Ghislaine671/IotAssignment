#!/bin/bash
# ============================================
#  Quick Setup Script (Linux/Mac)
#  Creates venv and installs all dependencies
# ============================================

echo "=== Hand Gesture LED Control - First Time Setup ==="

if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

echo "Installing dependencies..."
./venv/bin/pip install -r requirements.txt

echo ""
echo "=== Setup Complete! ==="
echo "Run the app with:       ./run.sh"
echo "Run with mock ESP:      ./run_mock.sh"
echo "Run tests:              ./run_tests.sh"
