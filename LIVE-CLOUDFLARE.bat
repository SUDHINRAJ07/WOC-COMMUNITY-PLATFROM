@echo off
title WOC Platform - Cloudflare Live Tunnel
color 0B
echo ========================================================
echo       THE WOC - CLOUDFLARE PUBLIC LIVE TUNNEL
echo ========================================================
echo.
echo [1/2] Checking if local WOC server is running on port 4317...
netstat -ano | findstr 127.0.0.1:4317 >nul 2>&1
if %errorlevel% neq 0 (
    echo Local server is not running. Starting WOC servers first...
    powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0woc-platform\start-woc.ps1"
) else (
    echo Local server is already running!
)

echo.
echo [2/2] Connecting to Cloudflare Global Network...
echo.
echo ========================================================
echo  LOOK BELOW for your live HTTPS URL:
echo  (It will look like: https://something.trycloudflare.com)
echo.
echo  Keep this window OPEN while sharing the live link.
echo  To stop sharing, close this window or press Ctrl+C.
echo ========================================================
echo.

cd /d "%~dp0"
"%~dp0cloudflared.exe" tunnel --url http://127.0.0.1:4317
pause
