@echo off
REM =============================================================
REM  BiscuitAI — Start Both Servers in separate windows
REM =============================================================
echo  Launching BiscuitAI...

start "BiscuitAI Backend" cmd /k "call venv\Scripts\activate.bat && set PYTHONPATH=%CD% && python backend\app.py"
timeout /t 3 /nobreak >nul
start "BiscuitAI Frontend" cmd /k "cd frontend && npm start"

echo.
echo  Both servers launching in separate windows.
echo  Backend : http://localhost:5000
echo  Frontend: http://localhost:3000
echo.
