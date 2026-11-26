@echo off
title WOC Platform - Local Server Launcher
color 0A
echo ========================================================
echo          THE WOC - WIND OF CHANGE PLATFORM
echo ========================================================
echo.
echo [1/2] Starting WOC Frontend and Backend...
cd /d "%~dp0woc-platform"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0woc-platform\start-woc.ps1"
if errorlevel 1 (
    echo WOC startup did not complete. Check the message above.
    pause
    exit /b 1
)

echo.
echo [2/2] Opening WOC Platform in your default browser...
start http://127.0.0.1:4317

echo.
echo ========================================================
echo  SUCCESS! WOC Platform is running:
echo   - Website : http://127.0.0.1:4317
echo   - API     : http://127.0.0.1:8317/api/health/
echo.
echo  To STOP the servers later, double-click STOP.bat
echo ========================================================
echo.
pause
