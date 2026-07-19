#!/bin/bash

# ============================================================================
# setup.sh - One-command environment setup for macOS
#
# This script:
#   1. Creates a Python virtual environment in ./venv (if not already present)
#   2. Activates it
#   3. Upgrades pip
#   4. Installs all packages from requirements.txt
#   5. Installs Playwright's Chromium browser binary
#
# Usage:
#   ./setup.sh
#
# After it finishes, activate the environment in future sessions with:
#   source venv/bin/activate
# ============================================================================

echo "=============================================="
echo " GeM Manpower Tender Scanner - Environment Setup"
echo "=============================================="

# Step 1: Create virtual environment if it doesn't already exist
if [ ! -d "venv" ]; then
    echo "[1/5] Creating virtual environment in ./venv ..."
    python3 -m venv venv
else
    echo "[1/5] Virtual environment already exists - skipping creation."
fi

# Step 2: Activate the virtual environment
echo "[2/5] Activating virtual environment ..."
source venv/bin/activate

# Step 3: Upgrade pip
echo "[3/5] Upgrading pip ..."
python -m pip install --upgrade pip

# Step 4: Install project dependencies
echo "[4/5] Installing dependencies from requirements.txt ..."
pip install -r requirements.txt

# Step 5: Install Playwright's bundled Chromium browser
echo "[5/5] Installing Playwright Chromium browser ..."
playwright install chromium

echo "=============================================="
echo " Setup complete!"
echo
echo " To activate this environment in future sessions, run:"
echo "   source venv/bin/activate"
echo
echo " Then start the scanner with:"
echo "   python app.py"
echo "=============================================="
