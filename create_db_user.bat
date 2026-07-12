@echo off
echo Creating PostgreSQL user for Odoo...
psql -U postgres -c "CREATE USER odoo WITH PASSWORD 'odoo' CREATEDB SUPERUSER;"
echo.
echo Done! User 'odoo' created with password 'odoo'
pause
