#!/usr/bin/env bash
set -e
echo "============================================================"
echo "  APIx Platform - Smart India Hackathon 2026 - Team CodeCrew"
echo "============================================================"
echo ""
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] python3 could not be found. Please install Python 3.10+."
    exit 1
fi
if [ ! -d ".venv" ]; then
    echo "[*] Creating Python virtual environment in .venv..."
    python3 -m venv .venv
fi
echo "[*] Activating virtual environment..."
source .venv/bin/activate
echo "[*] Installing dependencies from requirements.txt..."
pip install -r requirements.txt --quiet
echo "[*] Checking database state..."
python scripts/init_db.py
echo ""
echo "============================================================"
echo "  Launching FastAPI (Port 8000) and Streamlit (Port 8501)..."
echo "============================================================"
echo ""
python scripts/start_services.py
