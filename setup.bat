@echo off
REM ============================================================================
REM setup.bat - One-command environment setup for Windows
REM
REM This script:
REM   1. Creates a Python virtual environment in .\venv (if not already present)
REM   2. Activates it
REM   3. Upgrades pip
REM   4. Installs all packages from requirements.txt
REM   5. Installs Playwright's Chromium browser binary
REM
REM Usage (from Command Prompt or PowerShell):
REM   setup.bat
REM
REM After it finishes, activate the environment in future sessions with:
REM   venv\Scripts\activate.bat
REM ============================================================================

echo ==============================================
echo  GeM Manpower Tender Scanner - Environment Setup
echo ==============================================

REM Step 1: Create virtual environment if it doesn't already exist.
if not exist "venv\" (
    echo [1/5] Creating virtual environment in .\venv ...
    python -m venv venv
) else (
    echo [1/5] Virtual environment already exists - skipping creation.
)

REM Step 2: Activate the virtual environment for the rest of this script.
echo [2/5] Activating virtual environment ...
call venv\Scripts\activate.bat

REM Step 3: Upgrade pip to avoid install issues with older versions.
echo [3/5] Upgrading pip ...
python -m pip install --upgrade pip

REM Step 4: Install project dependencies.
echo [4/5] Installing dependencies from requirements.txt ...
pip install -r requirements.txt

REM Step 5: Install Playwright's bundled Chromium browser.
echo [5/5] Installing Playwright Chromium browser ...
playwright install chromium

echo ==============================================
echo  Setup complete!
echo.
echo  To activate this environment in future sessions, run:
echo    venv\Scripts\activate.bat
echo.
echo  Then start the scanner with:
echo    python app.py
echo ==============================================
