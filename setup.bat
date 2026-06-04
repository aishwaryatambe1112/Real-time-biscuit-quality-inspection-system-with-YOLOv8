@echo off
REM =============================================================
REM  BiscuitAI — Windows Setup Script
REM  Run this ONCE after cloning the project.
REM  Requirements: Python 3.10+, Node.js 18+, MySQL 8+
REM =============================================================

echo.
echo  =====================================================
echo    BiscuitAI Setup — Real-Time Inspection System
echo  =====================================================
echo.

REM ── Check Python ──────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Install Python 3.10+ from python.org
    pause
    exit /b 1
)
echo [OK] Python found

REM ── Check Node ────────────────────────────────────────────
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js not found. Install Node.js 18+ from nodejs.org
    pause
    exit /b 1
)
echo [OK] Node.js found

REM ── Check MySQL ───────────────────────────────────────────
mysql --version >nul 2>&1
if errorlevel 1 (
    echo [WARNING] mysql CLI not found in PATH.
    echo           Make sure MySQL 8+ is installed and running.
)

echo.
echo [STEP 1/4] Creating Python virtual environment...
if not exist "venv" (
    python -m venv venv
    echo [OK] venv created
) else (
    echo [SKIP] venv already exists
)

echo.
echo [STEP 2/4] Installing Python dependencies...
call venv\Scripts\activate.bat
pip install --upgrade pip --quiet
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] pip install failed. Check requirements.txt
    pause
    exit /b 1
)
echo [OK] Python packages installed

echo.
echo [STEP 3/4] Installing frontend dependencies...
cd frontend
call npm install
if errorlevel 1 (
    echo [ERROR] npm install failed
    pause
    exit /b 1
)
cd ..
echo [OK] Frontend packages installed

echo.
echo [STEP 4/4] Setting up database schema...
echo.
echo  Please enter your MySQL credentials to create the database:
set /p DB_USER=  MySQL username (default: root): 
if "%DB_USER%"=="" set DB_USER=root
set /p DB_PASS=  MySQL password: 

mysql -u %DB_USER% -p%DB_PASS% < database\schema.sql
if errorlevel 1 (
    echo [WARNING] Schema import had issues — may already exist or check credentials.
) else (
    echo [OK] Database schema applied
)

echo.
echo  =====================================================
echo    Setup Complete!
echo  =====================================================
echo.
echo  Next steps:
echo    1. Edit .env and fill in your credentials
echo    2. Run: start_backend.bat   (in one terminal)
echo    3. Run: start_frontend.bat  (in another terminal)
echo    4. Open http://localhost:3000
echo.
echo  Model files:
echo    After training, copy best.pt files to models/ folder:
echo      models\monaco_best.pt
echo      models\parle_best.pt
echo      models\marie_best.pt
echo.
pause
