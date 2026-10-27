#!/usr/bin/env bash
# Mac / Linux launcher - creates a virtual environment, installs packages, starts the dashboard.
set -e
cd "$(dirname "$0")"
PY=$(command -v python3 || command -v python || true)
if [ -z "$PY" ]; then
  echo "Python 3.9+ is required. Install it from https://www.python.org/downloads/"
  exit 1
fi
if [ ! -d ".venv" ]; then
  echo "Creating virtual environment..."
  "$PY" -m venv .venv
fi
source .venv/bin/activate
echo "Installing requirements..."
python -m pip install --quiet --upgrade pip
python -m pip install --quiet -r requirements.txt
echo "Starting dashboard at http://localhost:8501"
python -m streamlit run app.py
