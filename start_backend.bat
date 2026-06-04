@echo off
REM =============================================================
REM  BiscuitAI — Start Backend Server
REM  Run from project root: start_backend.bat
REM =============================================================
echo.
echo  Starting BiscuitAI Backend Server...
echo  Press Ctrl+C to stop.
echo.

if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found. Run setup.bat first.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat
set PYTHONPATH=%CD%
python backend\app.py
pause
