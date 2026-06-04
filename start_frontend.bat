@echo off
REM =============================================================
REM  BiscuitAI — Start Frontend (React)
REM  Run from project root: start_frontend.bat
REM =============================================================
echo.
echo  Starting BiscuitAI Frontend...
echo  Opens at http://localhost:3000
echo  Press Ctrl+C to stop.
echo.

if not exist "frontend\node_modules" (
    echo [ERROR] Frontend dependencies not installed. Run setup.bat first.
    pause
    exit /b 1
)

cd frontend
npm start
