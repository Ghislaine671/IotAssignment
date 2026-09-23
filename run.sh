#!/bin/bash
# ============================================
#  Run with REAL ESP32 or OFFLINE
#  Usage:  ./run.sh [ESP32_IP]
#  Example: ./run.sh 192.168.1.100
# ============================================

if [ "$1" = "offline" ] || [ -z "$1" ]; then
    if [ -z "$1" ]; then
        echo ""
        echo "=== Hand Gesture LED Control ==="
        echo ""
        echo "Usage Options:"
        echo "  ./run.sh 192.168.1.100   - Connect to ESP32 at that IP"
        echo "  ./run.sh offline         - Run camera only, no ESP32"
        echo "  ./run_mock.sh            - Run with mock ESP32 server"
        echo ""
        read -p "Enter ESP32 IP address (or press Enter for offline mode): " ESP_IP
        if [ -z "$ESP_IP" ]; then
            echo "Starting in OFFLINE mode (camera only)..."
            ./venv/bin/python app.py
        else
            echo "Starting with ESP32 at http://$ESP_IP ..."
            ./venv/bin/python app.py --esp32-url "http://$ESP_IP"
        fi
    else
        echo "Starting in OFFLINE mode (camera only)..."
        ./venv/bin/python app.py
    fi
else
    echo "Starting with ESP32 at http://$1 ..."
    ./venv/bin/python app.py --esp32-url "http://$1"
fi
