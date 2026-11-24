@echo off
title WOC Platform - Stop Servers
color 0C
echo ========================================================
echo           STOPPING WOC PLATFORM SERVERS
echo ========================================================
echo.
echo [1/2] Stopping project server processes...
cd /d "%~dp0woc-platform"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0woc-platform\stop-woc.ps1"

echo.
echo [2/2] Stopping any active Cloudflare tunnels...
taskkill /F /IM cloudflared.exe >nul 2>&1

echo.
echo ========================================================
echo  All WOC servers and tunnels have been STOPPED.
echo ========================================================
echo.
pause
