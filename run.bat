@echo off
echo ============================================
echo  TransitOps Fleet - Docker Manager
echo ============================================
echo.
echo  1. Start (first time setup)
echo  2. Start (already set up)
echo  3. Stop
echo  4. Reset everything (fresh install)
echo  5. View logs
echo.
set /p choice="Enter choice (1-5): "

if "%choice%"=="1" goto first_start
if "%choice%"=="2" goto start
if "%choice%"=="3" goto stop
if "%choice%"=="4" goto reset
if "%choice%"=="5" goto logs

:first_start
echo.
echo [1/3] Pulling Odoo 18 and PostgreSQL images...
docker-compose pull
echo.
echo [2/3] Starting containers...
docker-compose up -d
echo.
echo [3/3] Waiting 15 seconds for Odoo to initialize...
timeout /t 15 /nobreak
echo.
echo ✅ Done! Open your browser and go to:
echo    http://localhost:8069
echo.
echo    Database name : transitops
echo    Email         : admin@example.com
echo    Password      : admin
echo.
pause
goto end

:start
echo Starting containers...
docker-compose up -d
echo.
echo ✅ Odoo is running at http://localhost:8069
pause
goto end

:stop
echo Stopping containers...
docker-compose down
echo ✅ Stopped.
pause
goto end

:reset
echo ⚠  This will DELETE all data and start fresh!
set /p confirm="Type YES to confirm: "
if "%confirm%"=="YES" (
    docker-compose down -v
    docker-compose up -d
    echo ✅ Fresh instance started at http://localhost:8069
) else (
    echo Cancelled.
)
pause
goto end

:logs
docker-compose logs -f odoo
goto end

:end
