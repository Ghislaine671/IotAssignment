@echo off
REM ============================================
REM  Quick Setup Script (Windows)
REM  Creates venv and installs all dependencies
REM ============================================

echo === Hand Gesture LED Control - First Time Setup ===

IF NOT EXIST venv (
    echo Creating Python virtual environment...
    python -m venv venv
)

echo Installing dependencies...
call venv\Scripts\pip.exe install -r requirements.txt

echo.
echo === Setup Complete! ===
echo Run the app with:  run.bat
echo Run with mock ESP:  run_mock.bat
pause
