@echo off
REM ============================================
REM  Run Unit Tests
REM ============================================

echo === Running Unit Tests ===
echo.
call venv\Scripts\python.exe -m pytest tests/ -v
echo.
pause
