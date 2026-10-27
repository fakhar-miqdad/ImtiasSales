@echo off
REM Windows launcher - creates a virtual environment, installs packages, starts the dashboard.
cd /d "%~dp0"
where python >nul 2>nul
if errorlevel 1 (
  echo Python is not installed or not on PATH. Install Python 3.9+ from https://www.python.org/downloads/
  pause
  exit /b 1
)
if not exist .venv (
  echo Creating virtual environment...
  python -m venv .venv
)
call .venv\Scripts\activate.bat
echo Installing requirements...
python -m pip install --quiet --upgrade pip
python -m pip install --quiet -r requirements.txt
echo Starting dashboard - your browser will open at http://localhost:8501
python -m streamlit run app.py
pause
