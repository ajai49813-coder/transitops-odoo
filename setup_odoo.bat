@echo off
title TransitOps - Odoo 18 Setup
color 0A

echo ================================================
echo   TransitOps Fleet - Odoo 18 Setup Script
echo ================================================
echo.

:: ── Step 1: Check Python 3.12 ──────────────────────────────
echo [1/6] Checking Python 3.12...
py -3.12 --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo  ERROR: Python 3.12 not found!
    echo  Please download and install it from:
    echo  https://www.python.org/downloads/release/python-3129/
    echo  Make sure to check "Add Python to PATH" during install.
    echo.
    pause
    exit /b 1
)
py -3.12 --version
echo  Python 3.12 found!
echo.

:: ── Step 2: Check PostgreSQL ────────────────────────────────
echo [2/6] Checking PostgreSQL...
where psql >nul 2>&1
if errorlevel 1 (
    echo  ERROR: psql not found in PATH.
    echo  Add PostgreSQL bin folder to PATH:
    echo  C:\Program Files\PostgreSQL\16\bin
    pause
    exit /b 1
)
echo  PostgreSQL found!
echo.

:: ── Step 3: Create Odoo DB user ─────────────────────────────
echo [3/6] Creating PostgreSQL user 'odoo'...
psql -U postgres -c "CREATE USER odoo WITH PASSWORD 'odoo' CREATEDB;" 2>nul
echo  (Ignore 'already exists' error - that is fine)
echo.

:: ── Step 4: Clone Odoo 18 ───────────────────────────────────
echo [4/6] Cloning Odoo 18 Community source...
if exist "odoo18" (
    echo  Odoo 18 folder already exists, skipping clone.
) else (
    echo  This will take 5-10 minutes depending on internet speed...
    git clone https://github.com/odoo/odoo.git --depth=1 --branch=18.0 odoo18
    if errorlevel 1 (
        echo  ERROR: Git clone failed. Check your internet connection.
        pause
        exit /b 1
    )
)
echo  Odoo 18 source ready!
echo.

:: ── Step 5: Create virtual environment ─────────────────────
echo [5/6] Creating Python virtual environment...
if exist "odoo18\venv" (
    echo  Virtual environment already exists, skipping.
) else (
    py -3.12 -m venv odoo18\venv
    echo  Installing Odoo dependencies (this takes 3-5 minutes)...
    odoo18\venv\Scripts\pip install --upgrade pip setuptools wheel
    odoo18\venv\Scripts\pip install -r odoo18\requirements.txt
    :: Extra packages sometimes missing from requirements.txt
    odoo18\venv\Scripts\pip install psycopg2-binary Pillow
)
echo  Virtual environment ready!
echo.

:: ── Step 6: Create odoo.conf ────────────────────────────────
echo [6/6] Creating Odoo configuration file...
if not exist "odoo18\odoo.conf" (
    (
        echo [options]
        echo db_host = localhost
        echo db_port = 5432
        echo db_user = odoo
        echo db_password = odoo
        echo addons_path = %CD%\odoo18\addons,%CD%\custom_addons
        echo http_port = 8069
        echo logfile = %CD%\odoo18\odoo.log
        echo log_level = info
        echo dev_mode = all
    ) > odoo18\odoo.conf
)
echo  Config file created!
echo.

:: ── Copy module to custom_addons ────────────────────────────
if not exist "custom_addons" mkdir custom_addons
if exist "transitops_fleet" (
    xcopy /E /I /Y transitops_fleet custom_addons\transitops_fleet >nul
    echo  Module copied to custom_addons!
)

echo.
echo ================================================
echo   SETUP COMPLETE!
echo ================================================
echo.
echo   Next step: Run start_odoo.bat
echo.
pause
