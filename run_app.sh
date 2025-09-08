#!/usr/bin/env bash
set -euo pipefail

# Resource Allocation System - launcher script
# - Creates/activates a virtual environment
# - Installs dependencies
# - Launches the GUI application

# Resolve project root (directory of this script)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

log() { printf "[%s] %s\n" "$(date +%H:%M:%S)" "$*"; }

# Pick Python interpreter
if command -v python3 >/dev/null 2>&1; then
  PYTHON=python3
elif command -v python >/dev/null 2>&1; then
  PYTHON=python
else
  echo "Python is not installed or not on PATH" >&2
  exit 1
fi

# Choose venv directory (env var override -> .venv -> venv -> create venv)
VENV_DIR_DEFAULT="$SCRIPT_DIR/venv"
if [[ -n "${VENV_DIR:-}" ]]; then
  VENV_DIR="$VENV_DIR"
elif [[ -d "$SCRIPT_DIR/.venv" ]]; then
  VENV_DIR="$SCRIPT_DIR/.venv"
elif [[ -d "$SCRIPT_DIR/venv" ]]; then
  VENV_DIR="$SCRIPT_DIR/venv"
else
  VENV_DIR="$VENV_DIR_DEFAULT"
fi

# Create venv if missing
if [[ ! -d "$VENV_DIR" ]]; then
  log "Creating virtual environment at $VENV_DIR"
  "$PYTHON" -m venv "$VENV_DIR"
fi

# Activate venv (POSIX shells)
if [[ -f "$VENV_DIR/bin/activate" ]]; then
  # shellcheck disable=SC1090
  source "$VENV_DIR/bin/activate"
else
  echo "Could not find venv activation script at $VENV_DIR/bin/activate" >&2
  exit 1
fi

trap 'deactivate >/dev/null 2>&1 || true' EXIT

# Upgrade base tooling
log "Upgrading pip/setuptools/wheel"
python -m pip install --upgrade pip setuptools wheel

# Install dependencies if requirements exist
if [[ -f "$SCRIPT_DIR/requirements.txt" ]]; then
  log "Installing dependencies from requirements.txt"
  pip install -r "$SCRIPT_DIR/requirements.txt"
else
  log "No requirements.txt found; skipping dependency install"
fi

# Optional: Install macOS AppKit for dock icon enhancement if on macOS
if [[ "$(uname -s)" == "Darwin" ]]; then
  if python - <<'PY'
import importlib.util
import sys
spec = importlib.util.find_spec('AppKit')
sys.exit(0 if spec else 1)
PY
  then
    log "AppKit already available (pyobjc)."
  else
    log "AppKit not found. You can install it with: pip install pyobjc (optional)"
  fi
fi

# Launch the GUI
log "Launching GUI application"
exec python gui_app.py

