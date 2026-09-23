#!/bin/bash
# ============================================
#  Run with MOCK ESP32 (no hardware needed)
#  Launches mock server + camera app together
# ============================================

echo "=== Starting Mock ESP32 Server + Camera App ==="
echo ""
echo "Mock server will run on http://127.0.0.1:5000"
echo ""

# Start mock server in background
./venv/bin/python mock_esp32.py --port 5000 &
MOCK_PID=$!

# Give mock server a moment to start
sleep 2

echo "Starting camera app..."
./venv/bin/python app.py --esp32-url http://127.0.0.1:5000

# When camera app exits, kill mock server
echo "Stopping mock server..."
kill $MOCK_PID 2>/dev/null
