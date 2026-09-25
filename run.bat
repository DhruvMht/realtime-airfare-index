@echo off
title APIx Platform - Team CodeCrew
echo ============================================================
echo   APIx Platform - Smart India Hackathon 2026 - Team CodeCrew
echo ============================================================
echo.
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.10+ from https://www.python.org/
    pause
    exit /b 1
)
if not exist ".venv" (
    echo [*] Creating virtual environment in .venv...
    python -m venv .venv
)
echo [*] Activating virtual environment...
call .venv\Scripts\activate.bat
echo [*] Installing / verifying dependencies...
pip install -r requirements.txt --quiet
echo [*] Checking database state...
python scripts\init_db.py
echo.
echo ============================================================
echo   Launching FastAPI (Port 8000) and Streamlit (Port 8501)...
echo ============================================================
echo.
python scripts\start_services.py
pause
