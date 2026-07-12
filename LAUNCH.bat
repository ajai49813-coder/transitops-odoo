@echo off
title TransitOps - Full Setup and Launch
color 0A

set BASE=C:\Users\ajai4\OneDrive\Desktop\transitops-odoo\transitops-odoo
set ODOO=%BASE%\odoo18
set VENV=%ODOO%\venv
set PYTHON=%VENV%\Scripts\python.exe
set PIP=%VENV%\Scripts\pip.exe
set ODOOBIN=%ODOO%\odoo-bin
set CONF=%BASE%\odoo.conf
set MODULE=%BASE%\transitops_fleet
set ADDONS=%ODOO%\custom_addons

echo.
echo =====================================================
echo   TransitOps Fleet - Auto Setup and Launch
echo =====================================================
echo.

:: ── Check Python 3.12 ────────────────────────────────────
echo [STEP 1] Checking Python 3.12...
py -3.12 --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo  ERROR: Python 3.12 is NOT installed.
    echo.
    echo  Please install it from:
    echo  https://www.python.org/downloads/release/python-3129/
    echo.
    echo  Download: python-3.12.9-amd64.exe
    echo  IMPORTANT: Tick "Add python.exe to PATH" during install
    echo.
    pause
    exit /b 1
)
echo  Python 3.12 OK
echo.

:: ── Check Odoo source ────────────────────────────────────
echo [STEP 2] Checking Odoo 18 source...
if not exist "%ODOOBIN%" (
    echo.
    echo  ERROR: Odoo 18 not found at %ODOO%
    echo.
    echo  Please run this command first:
    echo  git clone https://github.com/odoo/odoo.git --depth=1 --branch=18.0 odoo18
    echo.
    pause
    exit /b 1
)
echo  Odoo 18 source OK
echo.

:: ── Create virtual environment ───────────────────────────
echo [STEP 3] Setting up Python virtual environment...
if not exist "%VENV%\Scripts\activate.bat" (
    echo  Creating venv...
    py -3.12 -m venv "%VENV%"
    echo  Upgrading pip...
    "%PIP%" install --upgrade pip setuptools wheel --quiet
    echo  Installing Odoo requirements 3-5 mins...
    "%PIP%" install -r "%ODOO%\requirements.txt" --quiet
    echo  Installing extra packages...
    "%PIP%" install psycopg2-binary Pillow --quiet
    echo  Dependencies installed!
) else (
    echo  Virtual environment already exists, skipping.
)
echo.

:: ── Copy module ──────────────────────────────────────────
echo [STEP 4] Copying TransitOps module...
if not exist "%ADDONS%" mkdir "%ADDONS%"
xcopy /E /I /Y "%MODULE%" "%ADDONS%\transitops_fleet" >nul
echo  Module copied to custom_addons!
echo.

:: ── Write odoo.conf ──────────────────────────────────────
echo [STEP 5] Writing odoo.conf...
(
    echo [options]
    echo db_host = localhost
    echo db_port = 5432
    echo db_user = odoo
    echo db_password = odoo
    echo addons_path = %ADDONS%,%ODOO%\addons
    echo http_port = 8069
    echo log_level = warn
    echo dev_mode = all
) > "%CONF%"
echo  Config written!
echo.

:: ── Create DB user ───────────────────────────────────────
echo [STEP 6] Creating PostgreSQL user...
psql -U postgres -c "CREATE USER odoo WITH PASSWORD 'odoo' CREATEDB SUPERUSER;" >nul 2>&1
echo  DB user ready (ignore 'already exists' message)
echo.

:: ── Install Odoo + Module ────────────────────────────────
echo [STEP 7] Installing TransitOps database...
echo  This takes 2-3 minutes. Please wait...
"%PYTHON%" "%ODOOBIN%" -c "%CONF%" -d transitops -i transitops_fleet --without-demo=False --stop-after-init
if errorlevel 1 (
    echo.
    echo  ERROR during installation. Check the output above.
    pause
    exit /b 1
)
echo.
echo  Database installed successfully!
echo.

:: ── Start Server ─────────────────────────────────────────
echo [STEP 8] Starting Odoo server...
echo.
echo =====================================================
echo   SERVER IS STARTING...
echo.
echo   Open your browser and go to:
echo   http://localhost:8069
echo.
echo   Login  :  admin
echo   Password: admin
echo.
echo   Press Ctrl+C to stop the server
echo =====================================================
echo.

start "" "http://localhost:8069"
"%PYTHON%" "%ODOOBIN%" -c "%CONF%" -d transitops
