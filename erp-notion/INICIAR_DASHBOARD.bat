@echo off
echo ===================================================
echo    INICIANDO DASHBOARD FINANCIERO NOTION
echo ===================================================
echo.
echo 1. Iniciando servidor Python...
echo 2. Abriendo navegador...
echo.

start "" "http://localhost:8086"

python run_dashboard_v2.py

pause
