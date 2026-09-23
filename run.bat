@echo off
REM ============================================
REM  Run with REAL ESP32
REM  Usage:  run.bat [ESP32_IP]
REM  Example: run.bat 192.168.1.100
REM ============================================

IF "%~1"=="" (
    echo.
    echo === Hand Gesture LED Control ===
    echo.
    echo Usage Options:
    echo   run.bat 192.168.1.100    - Connect to ESP32 at that IP
    echo   run.bat offline          - Run camera only, no ESP32
    echo   run_mock.bat             - Run with mock ESP32 server
    echo.
    set /p ESP_IP="Enter ESP32 IP address (or press Enter for offline mode): "
    IF "!ESP_IP!"=="" goto OFFLINE
    goto CONNECT
) ELSE IF /I "%~1"=="offline" (
    goto OFFLINE
) ELSE (
    set ESP_IP=%~1
    goto CONNECT
)

:CONNECT
echo Starting with ESP32 at http://%ESP_IP% ...
call venv\Scripts\python.exe app.py --esp32-url http://%ESP_IP%
goto END

:OFFLINE
echo Starting in OFFLINE mode (camera only, no ESP32)...
call venv\Scripts\python.exe app.py
goto END

:END
pause
