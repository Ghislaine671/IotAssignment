@echo off
REM ============================================
REM  Run with MOCK ESP32 (no hardware needed)
REM  Launches mock server + camera app together
REM ============================================

echo === Starting Mock ESP32 Server + Camera App ===
echo.
echo Mock server will run on http://127.0.0.1:5000
echo Press Ctrl+C in each window to stop.
echo.

REM Start mock server in a new window
start "Mock ESP32 Server" cmd /k "cd /d %~dp0 && venv\Scripts\python.exe mock_esp32.py --port 5000"

REM Give mock server a moment to start
timeout /t 2 /nobreak >nul

REM Start the camera app connected to mock server
echo Starting camera app...
call venv\Scripts\python.exe app.py --esp32-url http://127.0.0.1:5000

pause
