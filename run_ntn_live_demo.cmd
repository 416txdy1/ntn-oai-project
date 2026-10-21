@echo off
setlocal
chcp 65001 >nul
title NTN WebRTC Live Demo
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0ntn_live_demo\launch.ps1" %*
set "DEMO_EXIT=%ERRORLEVEL%"
echo.
echo Live demo exit code: %DEMO_EXIT%
pause
exit /b %DEMO_EXIT%
