@echo off
title TransitOps - Odoo 18 Server
color 0B

echo ================================================
echo   TransitOps Fleet - Start Odoo Server
echo ================================================
echo.
echo  1. First time install (creates DB + installs module)
echo  2. Normal start (DB already exists)
echo  3. Upgrade module (after code changes)
echo  4. Open browser
echo.
set /p choice="Enter choice (1-4): "

if "%choice%"=="1" goto install
if "%choice%"=="2" goto start
if "%choice%"=="3" goto upgrade
if "%choice%"=="4" goto browser

:install
echo.
echo  Creating database and installing TransitOps module...
echo  This takes 2-3 minutes. Watch for any errors below.
echo.
odoo18\venv\Scripts\python odoo18\odoo-bin ^
    -c odoo18\odoo.conf ^
    -d transitops ^
    -i transitops_fleet ^
    --without-demo=False ^
    --stop-after-init
echo.
echo  Install complete! Now starting server...
goto start

:start
echo.
echo  Starting Odoo server...
echo  Open browser at: http://localhost:8069
echo  Login: admin / admin
echo.
echo  Press Ctrl+C to stop the server.
echo.
odoo18\venv\Scripts\python odoo18\odoo-bin ^
    -c odoo18\odoo.conf ^
    -d transitops
goto end

:upgrade
echo.
echo  Upgrading TransitOps module...
odoo18\venv\Scripts\python odoo18\odoo-bin ^
    -c odoo18\odoo.conf ^
    -d transitops ^
    -u transitops_fleet ^
    --stop-after-init
echo.
echo  Upgrade done! Run option 2 to start the server.
pause
goto end

:browser
start http://localhost:8069
goto end

:end
