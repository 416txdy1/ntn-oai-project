@echo off
setlocal
chcp 65001 >nul
title NTN Video and Audio Live Demo
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0ntn_live_demo\launch.ps1" -UseConfiguredSource %*
set "DEMO_EXIT=%ERRORLEVEL%"
echo.
echo Video/audio demo exit code: %DEMO_EXIT%
pause
exit /b %DEMO_EXIT%
