@echo off
setlocal
chcp 65001 >nul
title NTN Four-port MISO Video and Audio
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0ntn_live_demo\launch.ps1" -UseConfiguredSource -SpatialMode miso4-subarray %*
set "DEMO_EXIT=%ERRORLEVEL%"
echo.
echo MISO video/audio exit code: %DEMO_EXIT%
pause
exit /b %DEMO_EXIT%
