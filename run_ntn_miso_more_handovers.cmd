@echo off
setlocal
chcp 65001 >nul
title NTN Four-port MISO Handover Replay
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0ntn_live_demo\launch_replay.ps1" -SpatialMode miso4-subarray %*
set "DEMO_EXIT=%ERRORLEVEL%"
echo.
echo MISO handover replay exit code: %DEMO_EXIT%
pause
exit /b %DEMO_EXIT%
